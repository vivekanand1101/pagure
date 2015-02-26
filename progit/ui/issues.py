#-*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

import flask
import os
from math import ceil

import pygit2
from sqlalchemy.exc import SQLAlchemyError
from pygments import highlight
from pygments.lexers import guess_lexer
from pygments.lexers.text import DiffLexer
from pygments.formatters import HtmlFormatter


import progit.doc_utils
import progit.lib
import progit.forms
from progit import (APP, SESSION, LOG, __get_file_in_tree, cla_required,
                    is_repo_admin, authenticated)


## URLs

@APP.route('/<repo>/issue/<int:issueid>/add', methods=('GET', 'POST'))
@APP.route('/fork/<username>/<repo>/issue/<int:issueid>/add',
           methods=('GET', 'POST'))
def add_comment_issue(repo, issueid, username=None):
    ''' Add a comment to an issue. '''
    repo = progit.lib.get_project(SESSION, repo, user=username)

    if repo is None:
        flask.abort(404, 'Project not found')

    if not repo.issue_tracker:
        flask.abort(404, 'No issue tracker found for this project')

    issue = progit.lib.get_issue(SESSION, repo.id, issueid)

    if issue is None or issue.project != repo:
        flask.abort(404, 'Issue not found')

    form = progit.forms.AddIssueCommentForm()
    if form.validate_on_submit():
        comment = form.comment.data

        try:
            message = progit.lib.add_issue_comment(
                SESSION,
                issue=issue,
                comment=comment,
                user=flask.g.fas_user.username,
                ticketfolder=APP.config['TICKETS_FOLDER'],
            )
            SESSION.commit()
            flask.flash(message)
        except SQLAlchemyError, err:  # pragma: no cover
            SESSION.rollback()
            APP.logger.exception(err)
            flask.flash(str(err), 'error')

    return flask.redirect(flask.url_for(
        'view_issue', username=username, repo=repo.name, issueid=issueid))


@APP.route('/<repo>/issue/<int:issueid>/tag', methods=['POST'])
@APP.route('/fork/<username>/<repo>/issue/<int:issueid>/tag',
           methods=['POST'])
@cla_required
def add_tag_issue(repo, issueid, username=None):
    ''' Add a tag to an issue. '''
    repo = progit.lib.get_project(SESSION, repo, user=username)

    if repo is None:
        flask.abort(404, 'Project not found')

    if not repo.issue_tracker:
        flask.abort(404, 'No issue tracker found for this project')

    issue = progit.lib.get_issue(SESSION, repo.id, issueid)

    if issue is None or issue.project != repo:
        flask.abort(404, 'Issue not found')

    form = progit.forms.AddIssueTagForm()
    cat = None
    if form.validate_on_submit():
        tags = form.tag.data

        for tag in tags.split(','):
            tag = tag.strip()
            try:
                message = progit.lib.add_issue_tag(
                    SESSION,
                    issue=issue,
                    tag=tag,
                    user=flask.g.fas_user.username,
                    ticketfolder=APP.config['TICKETS_FOLDER'],
                )
                SESSION.commit()
                flask.flash(message)
            except SQLAlchemyError, err:  # pragma: no cover
                SESSION.rollback()
                LOG.error(err)
                flask.flash('Could not add tag: %s' % tag, 'error')

    return flask.redirect(flask.url_for(
        'view_issue', username=username, repo=repo.name, issueid=issueid))


@APP.route('/<repo>/issue/<int:issueid>/assigned', methods=['POST'])
@APP.route('/fork/<username>/<repo>/issue/<int:issueid>/assigned',
           methods=['POST'])
@cla_required
def add_assignee_issue(repo, issueid, username=None):
    ''' Add an assignee to an issue. '''
    repo = progit.lib.get_project(SESSION, repo, user=username)

    if repo is None:
        flask.abort(404, 'Project not found')

    if not repo.issue_tracker:
        flask.abort(404, 'No issue tracker found for this project')

    issue = progit.lib.get_issue(SESSION, repo.id, issueid)

    if issue is None or issue.project != repo:
        flask.abort(404, 'Issue not found')

    form = progit.forms.ConfirmationForm()
    cat = None
    if form.validate_on_submit():
        assignee = flask.request.form.get('assignee') or None

        try:
            message = progit.lib.add_issue_assignee(
                SESSION,
                issue=issue,
                assignee=assignee,
                user=flask.g.fas_user.username,
                ticketfolder=APP.config['TICKETS_FOLDER'],)
            if message:
                SESSION.commit()
                flask.flash(message)
        except progit.exceptions.ProgitException, err:
            flask.flash(str(err), 'error')
        except SQLAlchemyError, err:  # pragma: no cover
            SESSION.rollback()
            LOG.error(err)
            flask.flash('Could not assigned issue to: %s' % assignee, 'error')

    return flask.redirect(flask.url_for(
        'view_issue', username=username, repo=repo.name, issueid=issueid))


@APP.route('/<repo>/issue/<int:issueid>/blocked/<issuetype>',
           methods=['POST'])
@APP.route('/fork/<username>/<repo>/issue/<int:issueid>/blocked<issuetype>/',
           methods=['POST'])
@cla_required
def add_dependent_issue(repo, issueid, issuetype, username=None):
    ''' Add a blocked issue to an issue. '''
    repo = progit.lib.get_project(SESSION, repo, user=username)

    if repo is None:
        flask.abort(404, 'Project not found')

    if not repo.issue_tracker:
        flask.abort(404, 'No issue tracker found for this project')

    issue = progit.lib.get_issue(SESSION, repo.id, issueid)

    if issue is None or issue.project != repo:
        flask.abort(404, 'Issue not found')

    form = progit.forms.AddIssueDependencyForm()
    cat = None
    if form.validate_on_submit():
        blocked = form.depends.data
        issue_blocked = progit.lib.get_issue(SESSION, repo.id, blocked)
        if issue_blocked is None or issue_blocked.project != repo:
            flask.abort(404, 'Issue blocked not found')

        try:
            if issuetype == 'parent':
                message = progit.lib.add_issue_dependency(
                    SESSION,
                    issue=issue,
                    issue_blocked=issue_blocked,
                    user=flask.g.fas_user.username,
                    ticketfolder=APP.config['TICKETS_FOLDER'],)
            else:
                message = progit.lib.add_issue_dependency(
                    SESSION,
                    issue=issue_blocked,
                    issue_blocked=issue,
                    user=flask.g.fas_user.username,
                    ticketfolder=APP.config['TICKETS_FOLDER'],)
            if message:
                SESSION.commit()
                flask.flash(message)
        except progit.exceptions.ProgitException, err:
            flask.flash(str(err), 'error')
        except SQLAlchemyError, err:  # pragma: no cover
            SESSION.rollback()
            LOG.error(err)
            flask.flash(
                'Could not blocked issue: %s with %s' % (blocked, issue.id),
                'error')

    return flask.redirect(flask.url_for(
        'view_issue', username=username, repo=repo.name, issueid=issueid))


@APP.route('/<repo>/tag/<tag>/edit', methods=('GET', 'POST'))
@APP.route('/fork/<username>/<repo>/tag/<tag>/edit', methods=('GET', 'POST'))
@cla_required
def edit_tag(repo, tag, username=None):
    """ Edit the specified tag of a project.
    """
    repo = progit.lib.get_project(SESSION, repo, user=username)

    if not repo:
        flask.abort(404, 'Project not found')

    if not is_repo_admin(repo):
        flask.abort(
            403,
            'You are not allowed to add users to this project')

    form = progit.forms.AddIssueTagForm()
    if form.validate_on_submit():
        new_tag = form.tag.data

        msgs = progit.lib.edit_issue_tags(SESSION, repo, tag, new_tag)

        try:
            SESSION.commit()
            for msg in msgs:
                flask.flash(msg)
        except SQLAlchemyError, err:  # pragma: no cover
            SESSION.rollback()
            LOG.error(err)
            flask.flash('Could not edit tag: %s' % tag,'error')

        return flask.redirect(flask.url_for(
            '.view_settings', repo=repo.name, username=username)
        )

    return flask.render_template(
        'edit_tag.html',
        form=form,
        username=username,
        repo=repo,
        tag=tag,
    )


@APP.route('/<repo>/droptag/', methods=['POST'])
@APP.route('/fork/<username>/<repo>/droptag/', methods=['POST'])
@cla_required
def remove_tag(repo, username=None):
    """ Remove the specified tag from the project.
    """
    repo = progit.lib.get_project(SESSION, repo, user=username)

    if not repo:
        flask.abort(404, 'Project not found')

    if not is_repo_admin(repo):
        flask.abort(
            403,
            'You are not allowed to change the users for this project')

    form = progit.forms.AddIssueTagForm()
    if form.validate_on_submit():
        tags = form.tag.data
        tags = [tag.strip() for tag in tags.split(',')]

        msgs = progit.lib.remove_issue_tags(SESSION, repo, tags)

        try:
            SESSION.commit()
            for msg in msgs:
                flask.flash(msg)
        except SQLAlchemyError, err:  # pragma: no cover
            SESSION.rollback()
            LOG.error(err)
            flask.flash(
                'Could not remove tag: %s' % ','.join(tags), 'error')

    return flask.redirect(
        flask.url_for('.view_settings', repo=repo.name, username=username)
    )

@APP.route('/<repo>/issues')
@APP.route('/fork/<username>/<repo>/issues')
def view_issues(repo, username=None):
    """ List all issues associated to a repo
    """
    status = flask.request.args.get('status', None)
    tags = flask.request.args.getlist('tags', None)
    tags = [tag for tag in tags if tag]
    assignee = flask.request.args.get('assignee', None)
    author = flask.request.args.get('author', None)

    repo = progit.lib.get_project(SESSION, repo, user=username)

    if repo is None:
        flask.abort(404, 'Project not found')

    if not repo.issue_tracker:
        flask.abort(404, 'No issue tracker found for this project')

    if status is not None:
        if status.lower() == 'closed':
            issues = progit.lib.get_issues(
                SESSION,
                repo,
                closed=True,
                tags=tags,
                assignee=assignee,
                author=author,
            )
        else:
            issues = progit.lib.get_issues(
                SESSION,
                repo,
                status=status,
                tags=tags,
                assignee=assignee,
                author=author,
            )
    else:
        issues = progit.lib.get_issues(
            SESSION, repo, status='Open', tags=tags, assignee=assignee,
            author=author)

    tag_list = progit.lib.get_tags_of_project(SESSION, repo)

    return flask.render_template(
        'issues.html',
        select='issues',
        repo=repo,
        username=username,
        status=status,
        issues=issues,
        tags=tags,
        tag_list=tag_list,
    )


@APP.route('/<repo>/new_issue', methods=('GET', 'POST'))
@APP.route('/fork/<username>/<repo>/new_issue', methods=('GET', 'POST'))
@cla_required
def new_issue(repo, username=None):
    """ Create a new issue
    """
    repo = progit.lib.get_project(SESSION, repo, user=username)

    if repo is None:
        flask.abort(404, 'Project not found')

    status = progit.lib.get_issue_statuses(SESSION)
    form = progit.forms.IssueForm(status=status)
    if form.validate_on_submit():
        title = form.title.data
        content = form.issue_content.data

        try:
            message = progit.lib.new_issue(
                SESSION,
                repo=repo,
                title=title,
                content=content,
                user=flask.g.fas_user.username,
                ticketfolder=APP.config['TICKETS_FOLDER'],
            )
            SESSION.commit()
            flask.flash(message)
            return flask.redirect(flask.url_for(
                'view_issues', username=username, repo=repo.name))
        except progit.exceptions.ProgitException, err:
            flask.flash(str(err), 'error')
        except SQLAlchemyError, err:  # pragma: no cover
            SESSION.rollback()
            flask.flash(str(err), 'error')

    return flask.render_template(
        'new_issue.html',
        select='issues',
        form=form,
        repo=repo,
        username=username,
    )


@APP.route('/<repo>/issue/<int:issueid>', methods=('GET', 'POST'))
@APP.route('/fork/<username>/<repo>/issue/<int:issueid>',
           methods=('GET', 'POST'))
def view_issue(repo, issueid, username=None):
    """ List all issues associated to a repo
    """

    repo = progit.lib.get_project(SESSION, repo, user=username)

    if repo is None:
        flask.abort(404, 'Project not found')

    if not repo.issue_tracker:
        flask.abort(404, 'No issue tracker found for this project')

    issue = progit.lib.get_issue(SESSION, repo.id, issueid)

    if issue is None or issue.project != repo:
        flask.abort(404, 'Issue not found')

    status = progit.lib.get_issue_statuses(SESSION)

    form_comment = progit.forms.AddIssueCommentForm()
    form = form_tag = None
    if authenticated() and is_repo_admin(repo):
        form = progit.forms.UpdateIssueStatusForm(status=status)
        form_tag = progit.forms.AddIssueTagForm()

        if form.validate_on_submit():
            new_status = form.status.data
            if new_status == 'Fixed' and issue.parents:
                for parent in issue.parents:
                    print parent
                    if parent.status == 'Open':
                        flask.flash(
                            'You cannot close a ticket that has ticket '
                            'depending that are still open.',
                            'error')
                        return flask.redirect(flask.url_for(
                            'view_issue', repo=repo.name, username=username,
                            issueid=issueid))

            try:
                message = progit.lib.edit_issue(
                    SESSION,
                    issue=issue,
                    status=new_status,
                    ticketfolder=APP.config['TICKETS_FOLDER'],
                )
                SESSION.commit()
                flask.flash(message)
                url = flask.url_for(
                    'view_issue', username=username, repo=repo.name,
                    issueid=issueid)
                return flask.redirect(url)
            except SQLAlchemyError, err:  # pragma: no cover
                SESSION.rollback()
                flask.flash(str(err), 'error')
        elif flask.request.method == 'GET':
            form.status.data = issue.status

    return flask.render_template(
        'issue.html',
        select='issues',
        repo=repo,
        username=username,
        issue=issue,
        issueid=issueid,
        form=form,
        form_comment=form_comment,
        form_tag=form_tag,
    )


@APP.route('/<repo>/issue/<int:issueid>/edit', methods=('GET', 'POST'))
@APP.route('/fork/<username>/<repo>/issue/<int:issueid>/edit',
           methods=('GET', 'POST'))
@cla_required
def edit_issue(repo, issueid, username=None):
    """ Edit the specified issue
    """
    repo = progit.lib.get_project(SESSION, repo, user=username)

    if repo is None:
        flask.abort(404, 'Project not found')

    if not repo.issue_tracker:
        flask.abort(404, 'No issue tracker found for this project')

    if not is_repo_admin(repo):
        flask.abort(
            403, 'You are not allowed to edit issues for this project')

    issue = progit.lib.get_issue(SESSION, repo.id, issueid)

    if issue is None or issue.project != repo:
        flask.abort(404, 'Issue not found')

    status = progit.lib.get_issue_statuses(SESSION)
    form = progit.forms.IssueForm(status=status)
    if form.validate_on_submit():
        title = form.title.data
        content = form.issue_content.data
        status = form.status.data

        try:
            message = progit.lib.edit_issue(
                SESSION,
                issue=issue,
                title=title,
                content=content,
                status=status,
                ticketfolder=APP.config['TICKETS_FOLDER'],
            )
            SESSION.commit()
            flask.flash(message)
            url = flask.url_for(
                'view_issue', username=username,
                repo=repo.name, issueid=issueid)
            return flask.redirect(url)
        except progit.exceptions.ProgitException, err:
            flask.flash(str(err), 'error')
        except SQLAlchemyError, err:  # pragma: no cover
            SESSION.rollback()
            flask.flash(str(err), 'error')
    elif flask.request.method == 'GET':
        form.title.data = issue.title
        form.issue_content.data = issue.content
        form.status.data = issue.status

    return flask.render_template(
        'new_issue.html',
        select='issues',
        type='edit',
        form=form,
        repo=repo,
        username=username,
        issue=issue,
        issueid=issueid,
    )
