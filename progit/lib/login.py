#-*- coding: utf-8 -*-

"""
 (c) 2015 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

from progit.lib import model


def get_session_by_visitkey(session, sessionid):
    ''' Return a specified VisitUser via its session identifier (visit_key).

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.ProgitUserVisit
    ).filter(
        model.ProgitUserVisit.visit_key == sessionid
    )

    return query.first()


def get_groups(session):
    ''' Return the list of groups present in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.ProgitGroup
    ).order_by(
        model.ProgitGroup.group_name
    )

    return query.all()


def get_group(session, group):
    ''' Return a specific group for the specified group name.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.ProgitGroup
    ).filter(
        model.ProgitGroup.group_name == group
    ).order_by(
        model.ProgitGroup.group_name
    )

    return query.first()


def get_users_by_group(session, group):
    ''' Return the list of users for a specified group.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.User
    ).filter(
        model.User.id == model.ProgitUserGroup.user_id
    ).filter(
        model.ProgitUserGroup.group_id == model.ProgitGroup.id
    ).filter(
        model.ProgitGroup.group_name == group
    ).order_by(
        model.User.user
    )

    return query.all()


def get_user_group(session, userid, groupid):
    ''' Return a specific user_group for the specified group and user
    identifiers.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.ProgitUserGroup
    ).filter(
        model.ProgitUserGroup.user_id == userid
    ).filter(
        model.ProgitUserGroup.group_id == groupid
    )

    return query.first()