#-*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

import sqlalchemy as sa
import wtforms
from flask.ext import wtf
from sqlalchemy.orm import relation

from progit.hooks import BaseHook
from progit.model import BASE, Project
from progit import SESSION


class IrcTable(BASE):
    """ Stores information about the irc hook deployed on a project.

    Table -- hook_irc
    """

    __tablename__ = 'hook_irc'

    id = sa.Column(sa.Integer, primary_key=True)
    project_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('projects.id', onupdate='CASCADE'),
        nullable=False,
        unique=True,
        index=True)

    server = sa.Column(sa.Text, nullable=False)
    port = sa.Column(sa.Text, nullable=False)
    room = sa.Column(sa.Text, nullable=False)
    nick = sa.Column(sa.Text, nullable=True, default=None)
    nick_pass = sa.Column(sa.Text, nullable=True, default=None)
    active = sa.Column(sa.Boolean, nullable=False, default=False)
    join = sa.Column(sa.Boolean, nullable=False, default=True)
    ssl = sa.Column(sa.Boolean, nullable=False, default=True)

    project = relation(
        'Project', remote_side=[Project.id], backref='irc_hook')


class IrcForm(wtf.Form):
    ''' Form to configure the irc hook. '''
    server = wtforms.TextField(
        'Server <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    port = wtforms.TextField(
        'Port <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    room = wtforms.TextField(
        'Room <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    nick = wtforms.TextField(
        'Nick',
        [wtforms.validators.Optional()]
    )
    nick_pass = wtforms.TextField(
        'Nickserv Password',
        [wtforms.validators.Optional()]
    )

    active = wtforms.BooleanField(
        'Acive',
        [wtforms.validators.Optional()]
    )
    join = wtforms.BooleanField(
        'Message Without Join',
        [wtforms.validators.Optional()]
    )
    ssl = wtforms.BooleanField(
        'Use SSL',
        [wtforms.validators.Optional()]
    )


class Hook(BaseHook):
    ''' IRC hooks. '''

    name = 'IRC'
    form = IrcForm
    db_object = IrcTable
    backref = 'irc_hook'
    form_fields = [
        'server', 'port', 'room', 'nick', 'nick_pass', 'active', 'join',
        'ssl'
    ]
