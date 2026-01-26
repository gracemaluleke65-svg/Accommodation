from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
import stripe
from app import db
from app.models import Accommodation, Booking, Payment, Review
from app.forms import BookingForm, ReviewForm
from app.helpers import calculate_total_price

bp = Blueprint('bookings', __name__)


@bp.route('/book/<int:accommodation_id>', methods=['GET', 'POST'])
@login_required
def book_accommodation(accommodation_id):
    accommodation = Accommodation.query.get_or_404(accommodation_id)

    if not accommodation.is_available:
        flash('This accommodation is fully occupied', 'danger')
        return redirect(url_for('main.accommodation_detail', id=accommodation_id))

    existing_booking = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.accommodation_id == accommodation_id,
        Booking.status.in_(['pending', 'approved', 'paid'])
    ).first()

    if existing_booking:
        flash('You already have a booking for this accommodation', 'warning')
        return redirect(url_for('bookings.view_booking', booking_id=existing_booking.id))

    form = BookingForm()
    if form.validate_on_submit():
        total_price = calculate_total_price(
            accommodation.price_per_month,
            form.duration.data,
            form.period.data if form.duration.data == 'semester' else None,
        )

        booking = Booking(
            user_id=current_user.id,
            accommodation_id=accommodation_id,
            duration=form.duration.data,
            period=form.period.data if form.duration.data == 'semester' else None,
            payment_responsible=form.payment_responsible.data,
            total_price=total_price,
            status='approved',
        )

        accommodation.current_occupancy += 1
        if accommodation.current_occupancy >= accommodation.capacity:
            accommodation.status = 'fully_occupied'

        db.session.add(booking)
        db.session.commit()
        flash('Booking approved! Please proceed to payment.', 'success')
        return redirect(url_for('bookings.payment', booking_id=booking.id))

    return render_template(
        'bookings/apply.html',
        form=form,
        accommodation=accommodation,
        user=current_user,
    )


@bp.route('/bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(
        Booking.created_at.desc()
    ).all()
    return render_template('bookings/my_bookings.html', bookings=bookings)


@bp.route('/booking/<int:booking_id>')
@login_required
def view_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    return render_template('bookings/booking_detail.html', booking=booking)


@bp.route('/payment/<int:booking_id>')
@login_required
def payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    if booking.status != 'approved':
        flash('Booking must be approved before payment', 'warning')
        return redirect(url_for('bookings.view_booking', booking_id=booking_id))

    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': 'zar',
                    'product_data': {
                        'name': booking.accommodation.title,
                        'description': f'Booking #{booking.id} – {booking.duration} period',
                    },
                    'unit_amount': int(booking.total_price * 100),
                },
                'quantity': 1,
            }],
            metadata={
                'booking_id': booking.id,
                'user_id': current_user.id
            },
            customer_email=current_user.email,
            success_url=url_for('bookings.payment_success',
                              booking_id=booking.id,
                              _external=True),
            cancel_url=url_for('bookings.view_booking',
                             booking_id=booking.id,
                             _external=True),
        )
    except Exception as e:
        current_app.logger.error(f'Stripe Checkout error: {e}')
        flash('Payment system error. Please try again.', 'danger')
        return redirect(url_for('bookings.view_booking', booking_id=booking_id))

    booking.stripe_session_id = session.id
    booking.stripe_payment_intent_id = session.payment_intent
    db.session.commit()
    return redirect(session.url, code=303)


# --------------  STRIPED-DOWN SUCCESS ROUTE  --------------
@bp.route('/payment-success/<int:booking_id>')
@login_required
def payment_success(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))

    # 1.  Already paid?  Just show the page.
    if booking.status == 'paid':
        flash('Payment successful! Thank you for your booking.', 'success')
        return render_template('bookings/payment_success.html', booking=booking)

    # 2.  Mark booking paid
    booking.status = 'paid'
    db.session.add(booking)

    # 3.  Record payment only if NOT present
    exists = Payment.query.filter_by(booking_id=booking_id).first()
    if not exists:
        payment = Payment(
            booking_id=booking_id,
            stripe_payment_id=booking.stripe_payment_intent_id or f'local_{booking.id}',
            amount=booking.total_price,
            status='succeeded',
        )
        db.session.add(payment)

    db.session.commit()
    flash('Payment successful! Thank you for your booking.', 'success')
    return render_template('bookings/payment_success.html', booking=booking)


@bp.route('/review/<int:accommodation_id>', methods=['GET', 'POST'])
@login_required
def add_review(accommodation_id):
    accommodation = Accommodation.query.get_or_404(accommodation_id)

    paid_booking = Booking.query.filter_by(
        user_id=current_user.id,
        accommodation_id=accommodation_id,
        status='paid',
    ).first()
    if not paid_booking:
        flash('You need to have a paid booking to review this accommodation', 'warning')
        return redirect(url_for('main.accommodation_detail', id=accommodation_id))

    existing = Review.query.filter_by(
        user_id=current_user.id,
        accommodation_id=accommodation_id,
    ).first()
    if existing:
        flash('You have already reviewed this accommodation', 'info')
        return redirect(url_for('main.accommodation_detail', id=accommodation_id))

    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(
            user_id=current_user.id,
            accommodation_id=accommodation_id,
            rating=form.rating.data,
            comment=form.comment.data,
        )
        db.session.add(review)
        db.session.commit()
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('main.accommodation_detail', id=accommodation_id))

    return render_template(
        'bookings/add_review.html',
        form=form,
        accommodation=accommodation,
    )