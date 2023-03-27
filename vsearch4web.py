from flask import Flask, render_template, request, escape, session, copy_current_request_context
from vsearch import search4letters
from DBcm import UseDatabase, ConnectionError1, CredentialsError, SQLError
from checker import check_logged_in
from threading import Thread
from time import sleep

app = Flask(__name__)
app.secret_key = 'YouWillNeverGuess'
app.config['dbconfig'] = {'host': '127.0.0.1',
                          'user': 'root',
                          'password': '1',
                          'database': 'vsearchlogDB'
                          }




@app.route('/login')
def do_login() -> str:
    session['logged_in'] = True
    return 'You are now logged in!'


@app.route('/logout')
def do_logout() -> str:
    session.pop('logged_in')
    return 'You are now logged out!'


@app.route('/search4', methods=['POST'])
def do_search() -> 'html':
    @copy_current_request_context
    def log_request(req: 'flask_request', res: str) -> None:
        sleep(3)
        with UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = '''insert into log
                    (phrase, letters, ip, browser_string, results)
                    values
                    (%s, %s, %s, %s, %s)'''
            cursor.execute(_SQL,
                           (req.form['phrase'], req.form['letters'], req.remote_addr, str(req.user_agent), str(res)))

    phrase = request.form['phrase']
    letters = request.form['letters']
    title = 'Here are the results:'
    results = search4letters(phrase, letters)
    if results == set():
        results = 'Таких букв нет'
    try:
        t = Thread(target=log_request, args=(request, results))
        t.start()
    except Exception as err:
        print('logging failed', str(err))
    return render_template('results.html',
                           the_phrase=phrase,
                           the_letters=letters,
                           the_title=title,
                           the_results=results,)


@app.route('/')
@app.route('/entry')
def entry_page() -> 'html':
    return render_template('entry.html', the_title='Welcome to search4letters on the web!')


@app.route('/viewlog')
@check_logged_in
def view_the_log() -> 'html':
    try:
        with UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = '''select phrase, letters, ip, browser_string, results from log'''
            cursor.execute(_SQL)
            contents = cursor.fetchall()
        titles = ('phrase', 'letters', 'remote addr', 'user agent', 'results')
        return render_template('viewlog.html',
                               the_title='View log',
                               the_row_titles=titles,
                               the_data=contents
                               )
    except ConnectionError1 as err:
        print('database on?', err)
    except CredentialsError as err:
        print('user/pass err', err)
    except SQLError as err:
        print('query err', err)
    except Exception as err:
        print('something wrong', str(err))
    return 'Error'


if __name__ == '__main__':
    app.run(port=5501, debug=True)
