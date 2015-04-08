from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from sqlalchemy import engine_from_config

from erglog.security import group_finder

from .models import (
    DBSession,
    Base,
    )


def main(global_config, **settings):
    # SQLAlchemy bits
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    # Pyramid bits
    authn_policy = AuthTktAuthenticationPolicy(
        'springtimeforhitlerandgermany', callback=group_finder)
    authz_policy = ACLAuthorizationPolicy()

    # Application configuration
    config = Configurator(settings=settings, root_factory='erglog.models.RootFactory')
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    ### Routes ###
    config.add_route('login', '/')
    config.add_route('logout', '/logout/')
    config.add_route('home', '/home/')
    config.add_route('admin', '/admin/')
    config.add_route('add-distance-erg', '/add-distance-erg/{erg_type_id}/{username}/')
    config.add_route('view-distance-individual', '/view-distance/{erg_type_id}/{username}/')
    config.add_route('add-time-erg', '/add-time-erg/{erg_type_id}/{username}/')
    config.add_route('view-time-individual', '/view-time/{erg_type_id}/{username}/')
    config.add_route('view-distance-group', '/view-distance-group/{erg_type_id}/')
    config.add_route('view-time-group', '/view-time-group/{erg_type_id}/')
    ##############
    config.scan()
    
    # Start application
    return config.make_wsgi_app()
