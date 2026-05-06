from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Auth
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # Game Core
    from app.routes.game import game_bp
    app.register_blueprint(game_bp, url_prefix='/api/game')

    from app.routes.galaxy import galaxy_bp
    app.register_blueprint(galaxy_bp, url_prefix='/api/game/<game_id>/galaxy')

    from app.routes.colony import colony_bp
    app.register_blueprint(colony_bp, url_prefix='/api/game/<game_id>/colony')

    from app.routes.fleet import fleet_bp
    app.register_blueprint(fleet_bp, url_prefix='/api/game/<game_id>/fleet')

    # Game Features
    from app.routes.research import research_bp
    app.register_blueprint(research_bp, url_prefix='/api/game/<game_id>/research')

    from app.routes.diplomacy import diplomacy_bp
    app.register_blueprint(diplomacy_bp, url_prefix='/api/game/<game_id>/diplomacy')

    from app.routes.combat import combat_bp
    app.register_blueprint(combat_bp, url_prefix='/api/game/<game_id>/combat')

    from app.routes.espionage import espionage_bp
    app.register_blueprint(espionage_bp, url_prefix='/api/game/<game_id>/espionage')

    from app.routes.leaders import leaders_bp
    app.register_blueprint(leaders_bp, url_prefix='/api/game/<game_id>/leaders')

    from app.routes.ship_design import ship_design_bp
    app.register_blueprint(ship_design_bp, url_prefix='/api/game/<game_id>/ship-design')

    from app.routes.cheat import cheat_bp
    app.register_blueprint(cheat_bp, url_prefix='/api/game/<game_id>/cheat')

    return app
