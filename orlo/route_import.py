from __future__ import print_function
import arrow
from flask import jsonify, request
from orlo import app
from orlo.orm import db, Package, Release, PackageResult, ReleaseNote
from orlo.views import _validate_request_json
from orlo.util import list_to_string

__author__ = 'alforbes'


@app.route('/import', methods=['GET'])
@app.route('/import/release', methods=['GET'])
def get_import():
    """
    Display a useful message on how to import

    :status 200:
    """

    msg = 'This is the orlo import url'
    return jsonify(message=msg), 200


@app.route('/import/release', methods=['POST'])
def post_import():
    """
    Import a release

    The document must describe a full release, example:
    {
        'notes': ['note1', 'note2'],
        'platforms': ['test_platform'],
        'ftime': '2015-11-18T19:21:12Z',
        'stime': '2015-11-18T19:21:12Z',
        'team': 'test team',
        'references': ['TestTicket-123'],
        'packages': [
            {
                'status': 'SUCCESSFUL',
                'name': 'test-package',
                'version': '1.2.3',
                'ftime': '2015-11-18T19:21:12Z',
                'stime': '2015-11-18T19:21:12Z',
                'rollback': 'false',
                'diff_url': None,
            }
        ],
        'user': 'testuser'
    }

    :status 200: The release was accepted
    """

    _validate_request_json(request)

    release = Release(
        platforms=request.json.get('platforms'),
        user=request.json.get('user'),
        team=request.json.get('team', None),
        references=request.json.get('references'),
    )

    release.ftime = arrow.get(request.json.get('ftime'))
    release.stime = arrow.get(request.json.get('stime'))
    release.duration = release.ftime - release.stime

    db.session.add(release)

    if request.json.get('notes'):
        for n in request.json.get('notes'):
            note = ReleaseNote(release.id, n)
            db.session.add(note)

    for p in request.json.get('packages'):
        package = Package(
            release_id=release.id,
            name=p['name'],
            version=p['version'],
        )
        package.stime = arrow.get(p['stime'])
        package.ftime = arrow.get(p['ftime'])
        package.duration = package.ftime - package.stime
        package.rollback = p['rollback']
        package.status = p['status']
        package.diff_url = p['diff_url']

        db.session.add(package)

    db.session.commit()

    return jsonify(release_id=release.id), 200


