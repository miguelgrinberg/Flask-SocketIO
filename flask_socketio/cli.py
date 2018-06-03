import os
import sys

from flask.cli import pass_script_info, get_debug_flag, run_command
import click


@click.command()
@click.option('--host', '-h', default='127.0.0.1',
              help='The interface to bind to.')
@click.option('--port', '-p', default=5000,
              help='The port to bind to.')
@click.option('--reload/--no-reload', default=None,
              help='Enable or disable the reloader.  By default the reloader '
              'is active if debug is enabled.')
@click.option('--debugger/--no-debugger', default=None,
              help='Enable or disable the debugger.  By default the debugger '
              'is active if debug is enabled.')
@click.option('--eager-loading/--lazy-loader', default=None,
              help='Enable or disable eager loading.  By default eager '
              'loading is enabled if the reloader is disabled.')
@click.option('--with-threads/--without-threads', is_flag=True,
              help='These options are only supported for compatibility with '
              'the original Flask local development server and are ignored.')
@pass_script_info
def run(info, host, port, reload, debugger, eager_loading, with_threads):
    """Runs a local development server for the Flask-SocketIO application.

    The reloader and debugger are by default enabled if the debug flag of
    Flask is enabled and disabled otherwise.
    """
    debug = get_debug_flag()
    if reload is None:
        reload = bool(debug)
    if debugger is None:
        debugger = bool(debug)
    if eager_loading is None:
        eager_loading = not reload

    # Extra startup messages.  This depends a bit on Werkzeug internals to
    # not double execute when the reloader kicks in.
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # If we have an import path we can print it out now which can help
        # people understand what's being served.  If we do not have an
        # import path because the app was loaded through a callback then
        # we won't print anything.
        if info.app_import_path is not None:
            print(' * Serving Flask-SocketIO app "%s"' % info.app_import_path)
        if debug is not None:
            print(' * Forcing debug mode %s' % (debug and 'on' or 'off'))
    else:
        # if this is the child process of the reloader, then make sure we don't
        # start the reloader once again
        reload = False

    def run_server():
        app = info.load_app()
        if 'socketio' not in app.extensions:
            # flask-socketio is installed, but it isn't in this application
            # so we invoke Flask's original run command
            run_index = sys.argv.index('run')
            sys.argv = sys.argv[run_index:]
            return run_command()
        socketio = app.extensions['socketio']
        socketio.run(app, host=host, port=port, debug=debugger,
                     use_reloader=False, log_output=debugger)

    if reload:
        from werkzeug.serving import run_with_reloader
        run_with_reloader(run_server)
    else:
        run_server()
