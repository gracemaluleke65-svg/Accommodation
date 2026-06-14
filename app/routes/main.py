from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Accommodation, Favorite, Booking
from app.forms import SearchForm
from app.helpers import get_amenities_icons

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    featured = Accommodation.query.filter_by(status='available')\
        .order_by(db.func.random()).limit(3).all()
    return render_template('main/index.html', featured=featured)

@bp.route('/accommodations')
def accommodations():
    page = request.args.get('page', 1, type=int)
    form = SearchForm()

    query = Accommodation.query

    room_type = request.args.get('room_type')
    if room_type:
        query = query.filter_by(room_type=room_type)

    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    if min_price is not None:
        query = query.filter(Accommodation.price_per_month >= min_price)
    if max_price is not None:
        query = query.filter(Accommodation.price_per_month <= max_price)

    amenities_icons = get_amenities_icons()

    accommodations = query.filter_by(status='available')\
        .order_by(Accommodation.created_at.desc())\
        .paginate(page=page, per_page=12, error_out=False)

    return render_template('main/accommodations.html', 
                         accommodations=accommodations,
                         form=form,
                         amenities_icons=amenities_icons)

@bp.route('/accommodations/<int:id>')
def accommodation_detail(id):
    accommodation = Accommodation.query.get_or_404(id)
    amenities_icons = get_amenities_icons()

    is_favorite = False
    if current_user.is_authenticated:
        is_favorite = Favorite.query.filter_by(
            user_id=current_user.id,
            accommodation_id=id
        ).first() is not None

    reviews = accommodation.reviews

    return render_template('main/accommodation_detail.html',
                         accommodation=accommodation,
                         is_favorite=is_favorite,
                         reviews=reviews,
                         amenities_icons=amenities_icons)

@bp.route('/toggle_favorite/<int:accommodation_id>', methods=['POST'])
@login_required
def toggle_favorite(accommodation_id):
    """Temporarily disabled - shows coming soon message"""
    flash('Favorites feature coming soon!', 'info')
    return redirect(request.referrer or url_for('main.accommodation_detail', id=accommodation_id))

@bp.route('/favorites')
@login_required
def favorites():
    """Temporarily disabled - redirects with message"""
    flash('Favorites feature coming soon!', 'info')
    return redirect(url_for('main.accommodations'))

@bp.route('/about')
def about():
    return render_template('main/about.html')

@bp.route('/contact')
def contact():
    return render_template('main/contact.html')