# IMPORTS
import logging

from flask import Blueprint, render_template, request, flash
from sqlalchemy.orm import make_transient
from flask_login import login_required, current_user

from app import db
from models import Draw
from cryptography.fernet import Fernet

from functools import wraps
# CONFIG
lottery_blueprint = Blueprint('lottery', __name__, template_folder='templates')

# Temporary PostKey
master_post = Fernet.generate_key()

# Role definitions
def requires_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                return render_template('errors/403.html')
            return f(*args, **kwargs)
        return wrapped
    return wrapper


# VIEWS
# view lottery page
@lottery_blueprint.route('/lottery')
@login_required
@requires_roles('user')
def lottery():
    return render_template('lottery/lottery.html')


# add user draw
@lottery_blueprint.route('/add_draw', methods=['POST'])
@login_required
@requires_roles('user')
def add_draw():

    submitted_draw = ''
    temp_num = 0
    temp_str = ''

    # take input from submission fields

    for i in range(6):

        # enter value to temporary string
        temp_str = request.form.get('no' + str(i + 1)) + ' '

        # check whether string is empty
        if temp_str == ' ':
            flash('No fields can be left empty!!!')
            return lottery()

        # if not empty convert to integer
        temp_num = int(temp_str)

        # check whether value is between 1 and 60
        if 1 <= temp_num <= 60:
            submitted_draw += str(temp_num)
        else:
            flash('Not a valid sequence!!! The numbers in the field should hold a value between 1 and 60!!!')
            return lottery()

    submitted_draw.strip()

    # create a new draw with the form data.
    new_draw = Draw(user_id=current_user.id, numbers=submitted_draw, master_draw=False, lottery_round=0, postkey=master_post)  # TODO: update user_id [user_id=1 is a placeholder]

    # add the new draw to the database
    db.session.add(new_draw)
    db.session.commit()

    # re-render lottery.page
    flash('Draw %s submitted.' % submitted_draw)
    return lottery()


# view all draws that have not been played
@lottery_blueprint.route('/view_draws', methods=['POST'])
@login_required
@requires_roles('user')
def view_draws():
    # get all draws that have not been played [played=0]
    playable_draws = Draw.query.filter_by(been_played=False, id=current_user.id).all()  # TODO: filter playable draws for current user
    for playable_draw in playable_draws:
        make_transient(playable_draw)
        Draw.view_draw(master_post)
    # if playable draws exist
    if len(playable_draws) != 0:
        # re-render lottery page with playable draws
        return render_template('lottery/lottery.html', playable_draws=playable_draws)
    else:
        flash('No playable draws.')
        return lottery()


# view lottery results
@lottery_blueprint.route('/check_draws', methods=['POST'])
@login_required
@requires_roles('user')
def check_draws():
    # get played draws
    played_draws = Draw.query.filter_by(been_played=True, id=current_user.id).all()  # TODO: filter played draws for current user
    for played_draw in played_draws:
        make_transient(played_draw)
        Draw.view_draw(master_post)
    # if played draws exist
    if len(played_draws) != 0:
        return render_template('lottery/lottery.html', results=played_draws, played=True)

    # if no played draws exist [all draw entries have been played therefore wait for next lottery round]
    else:
        flash("Next round of lottery yet to play. Check you have playable draws.")
        return lottery()


# delete all played draws
@lottery_blueprint.route('/play_again', methods=['POST'])
@login_required
@requires_roles('user')
def play_again():
    Draw.query.filter_by(been_played=True, master_draw=False, id=current_user.id).delete(synchronize_session=False)
    db.session.commit()

    flash("All played draws deleted.")
    return lottery()

