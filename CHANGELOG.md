# Change Log

## [v2.0](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v2.0) (2016-01-10)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v1.2...v2.0)

**Implemented enhancements:**

- \[Missing Docs\] Can I deploy it with uwsgi? [\#168](https://github.com/miguelgrinberg/Flask-SocketIO/issues/168)

**Fixed bugs:**

- Basic auth with incorrect credentials doesn't seem to work correctly [\#197](https://github.com/miguelgrinberg/Flask-SocketIO/issues/197)
- Configuring SSL with eventlet [\#193](https://github.com/miguelgrinberg/Flask-SocketIO/issues/193)
- ssl configurations can not get passed to gevent [\#188](https://github.com/miguelgrinberg/Flask-SocketIO/issues/188)
- When the server does not support websocket, confusing errors are thrown if the client requests it [\#187](https://github.com/miguelgrinberg/Flask-SocketIO/issues/187)
- WebSocket connection fails with gevent when debug mode is on [\#177](https://github.com/miguelgrinberg/Flask-SocketIO/issues/177)

**Closed issues:**

- Properly handle user input in the example application [\#185](https://github.com/miguelgrinberg/Flask-SocketIO/issues/185)
- Attaching SocketIO to your app changes the logger configuration. [\#183](https://github.com/miguelgrinberg/Flask-SocketIO/issues/183)
- Provide a meaningful error message when the environment keys for eventlet and/or gevent are missing [\#180](https://github.com/miguelgrinberg/Flask-SocketIO/issues/180)

**Merged pull requests:**

- fixed ssl configuration issue [\#189](https://github.com/miguelgrinberg/Flask-SocketIO/pull/189) ([muatik](https://github.com/muatik))
- typo in \_\_init\_\_.py [\#182](https://github.com/miguelgrinberg/Flask-SocketIO/pull/182) ([lukeyeager](https://github.com/lukeyeager))
- Update index.rst [\#181](https://github.com/miguelgrinberg/Flask-SocketIO/pull/181) ([mitenka](https://github.com/mitenka))
- Fix spelling mistake [\#178](https://github.com/miguelgrinberg/Flask-SocketIO/pull/178) ([Liamraystanley](https://github.com/Liamraystanley))

## [v1.2](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v1.2) (2015-12-03)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v1.1...v1.2)

**Fixed bugs:**

- Failing to upgrade to websocket connection [\#175](https://github.com/miguelgrinberg/Flask-SocketIO/issues/175)

**Merged pull requests:**

- Replace assertTrue with assertEqual where possible. [\#174](https://github.com/miguelgrinberg/Flask-SocketIO/pull/174) ([jwg4](https://github.com/jwg4))

## [v1.1](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v1.1) (2015-11-19)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v1.0.0...v1.1)

**Implemented enhancements:**

- error when run exemple v1.0 [\#164](https://github.com/miguelgrinberg/Flask-SocketIO/issues/164)
- Get websocket data in exception handler [\#100](https://github.com/miguelgrinberg/Flask-SocketIO/issues/100)
- Broadcast message to all users except for sender [\#75](https://github.com/miguelgrinberg/Flask-SocketIO/issues/75)

**Fixed bugs:**

- sometimes, it takes really very long time to connect on heroku [\#171](https://github.com/miguelgrinberg/Flask-SocketIO/issues/171)
- broken pipe error shortly after a client disconnects [\#167](https://github.com/miguelgrinberg/Flask-SocketIO/issues/167)
- SocketIO Server Shutdown v1.0b4 [\#162](https://github.com/miguelgrinberg/Flask-SocketIO/issues/162)

**Closed issues:**

- Adding to Deployment Documentation [\#151](https://github.com/miguelgrinberg/Flask-SocketIO/issues/151)
- log\_file parameter is not logging to file [\#99](https://github.com/miguelgrinberg/Flask-SocketIO/issues/99)
- websocket using single browser tab [\#97](https://github.com/miguelgrinberg/Flask-SocketIO/issues/97)
- Gunicorn error : AttributeError: 'socket' object has no attribute 'cfg\_addr' [\#93](https://github.com/miguelgrinberg/Flask-SocketIO/issues/93)
- Segmentation Fault with requirements installed via pypi [\#92](https://github.com/miguelgrinberg/Flask-SocketIO/issues/92)
- Emitting to specific client [\#89](https://github.com/miguelgrinberg/Flask-SocketIO/issues/89)
- Installation instructions needed in docs [\#74](https://github.com/miguelgrinberg/Flask-SocketIO/issues/74)
- Document how to use ack callbacks [\#27](https://github.com/miguelgrinberg/Flask-SocketIO/issues/27)

## [v1.0.0](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v1.0.0) (2015-10-29)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v1.0b4...v1.0.0)

**Fixed bugs:**

- \[1.0b + eventlet\] cookies and sessions fall out of sync with main site thread [\#148](https://github.com/miguelgrinberg/Flask-SocketIO/issues/148)
- Sometimes upgrade to websocket is unsuccessful and blocks communication [\#144](https://github.com/miguelgrinberg/Flask-SocketIO/issues/144)

**Closed issues:**

- Circular imports and 1.0b4 [\#163](https://github.com/miguelgrinberg/Flask-SocketIO/issues/163)
- SocketIO Import Error [\#161](https://github.com/miguelgrinberg/Flask-SocketIO/issues/161)
- socketio.on decorator crashes if socketio.init\_app has not been called [\#159](https://github.com/miguelgrinberg/Flask-SocketIO/issues/159)

## [v1.0b4](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v1.0b4) (2015-10-18)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v1.0b3...v1.0b4)

**Fixed bugs:**

- Websocket transport not available when using eventlet with the gunicorn web server [\#153](https://github.com/miguelgrinberg/Flask-SocketIO/issues/153)
- Cannot associate a SocketIO instance with more than one application [\#146](https://github.com/miguelgrinberg/Flask-SocketIO/issues/146)
- \[1.0b\] Collistion in handling of SocketIO.run\(...\) arguments [\#145](https://github.com/miguelgrinberg/Flask-SocketIO/issues/145)

**Merged pull requests:**

- Fix custom resource path. [\#157](https://github.com/miguelgrinberg/Flask-SocketIO/pull/157) ([Bekt](https://github.com/Bekt))

## [v1.0b3](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v1.0b3) (2015-10-16)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v1.0b1...v1.0b3)

**Implemented enhancements:**

- Getting list of connected clients to a room [\#105](https://github.com/miguelgrinberg/Flask-SocketIO/issues/105)

**Fixed bugs:**

- Add the SocketIO middleware even when socketio.run is not used [\#152](https://github.com/miguelgrinberg/Flask-SocketIO/issues/152)
- \[1.0b\] SocketIO.on\(\) returns None [\#149](https://github.com/miguelgrinberg/Flask-SocketIO/issues/149)
- There is no equivalent of the "You need to use a gevent-socketio server" error message in v1.0 [\#147](https://github.com/miguelgrinberg/Flask-SocketIO/issues/147)

**Closed issues:**

- Disconnect unauthenticated users when using Flask-Login with v1.0 [\#154](https://github.com/miguelgrinberg/Flask-SocketIO/issues/154)
- Threading server selected over eventlet server \(v1.0b\) [\#150](https://github.com/miguelgrinberg/Flask-SocketIO/issues/150)
- on\_error should get the exception [\#142](https://github.com/miguelgrinberg/Flask-SocketIO/issues/142)
- all events come through to server at once [\#141](https://github.com/miguelgrinberg/Flask-SocketIO/issues/141)

## [v1.0b1](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v1.0b1) (2015-09-20)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v1.0a1...v1.0b1)

**Implemented enhancements:**

- v1.3.5 [\#104](https://github.com/miguelgrinberg/Flask-SocketIO/issues/104)

**Fixed bugs:**

- Running a SocketIO instance does not display anything [\#131](https://github.com/miguelgrinberg/Flask-SocketIO/issues/131)

**Closed issues:**

- build | failing ? [\#139](https://github.com/miguelgrinberg/Flask-SocketIO/issues/139)
- scheung38 [\#136](https://github.com/miguelgrinberg/Flask-SocketIO/issues/136)
- Integration with Flask-Twisted Library [\#135](https://github.com/miguelgrinberg/Flask-SocketIO/issues/135)
- Socketio swift + flask-socketio connect problems [\#132](https://github.com/miguelgrinberg/Flask-SocketIO/issues/132)

## [v1.0a1](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v1.0a1) (2015-08-09)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.6.0...v1.0a1)

**Implemented enhancements:**

- extra\_files in run\_with\_reloader? [\#120](https://github.com/miguelgrinberg/Flask-SocketIO/issues/120)

**Closed issues:**

- Provide bower support [\#127](https://github.com/miguelgrinberg/Flask-SocketIO/issues/127)
- Freeze when using debug options [\#124](https://github.com/miguelgrinberg/Flask-SocketIO/issues/124)
- When I use more than 1 worker chat is incredibly unreliable. [\#122](https://github.com/miguelgrinberg/Flask-SocketIO/issues/122)
- Can't pip install on OS X 10.10 [\#115](https://github.com/miguelgrinberg/Flask-SocketIO/issues/115)
- Greenlet exception after client disconnect [\#112](https://github.com/miguelgrinberg/Flask-SocketIO/issues/112)
- Providing proper access to Exceptions in on\_error handlers [\#110](https://github.com/miguelgrinberg/Flask-SocketIO/issues/110)
- ACK callback always None [\#108](https://github.com/miguelgrinberg/Flask-SocketIO/issues/108)
- Sending multiple emits buffers and sends all at once [\#106](https://github.com/miguelgrinberg/Flask-SocketIO/issues/106)

**Merged pull requests:**

- Pass along extra\_files param to run\_with\_reloader [\#121](https://github.com/miguelgrinberg/Flask-SocketIO/pull/121) ([bjamil](https://github.com/bjamil))
- tests for ack fix \#108 [\#111](https://github.com/miguelgrinberg/Flask-SocketIO/pull/111) ([patrickjahns](https://github.com/patrickjahns))
- return ack value \#fixes 108 [\#109](https://github.com/miguelgrinberg/Flask-SocketIO/pull/109) ([patrickjahns](https://github.com/patrickjahns))

## [v0.6.0](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.6.0) (2015-03-15)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.5.0...v0.6.0)

**Closed issues:**

- How to list all rooms available? Is there a way to identify the user that disconnected? [\#96](https://github.com/miguelgrinberg/Flask-SocketIO/issues/96)
- How to handle HTTPS with Flask-SocketIO ? [\#95](https://github.com/miguelgrinberg/Flask-SocketIO/issues/95)
- I get a AttributeError in SocketIOHandler,when I use the tool:ngrok and use IE11. Chrome is OK. [\#91](https://github.com/miguelgrinberg/Flask-SocketIO/issues/91)
- Gevent/SocketIO and SSL, EOF occurred in violation of protocol [\#88](https://github.com/miguelgrinberg/Flask-SocketIO/issues/88)

**Merged pull requests:**

- Add event information in flask request variable [\#101](https://github.com/miguelgrinberg/Flask-SocketIO/pull/101) ([Romainpaulus](https://github.com/Romainpaulus))
- Change README to reflect deprecated .ext import format [\#98](https://github.com/miguelgrinberg/Flask-SocketIO/pull/98) ([keyan](https://github.com/keyan))
- remove \</div\> tag [\#85](https://github.com/miguelgrinberg/Flask-SocketIO/pull/85) ([shinriyo](https://github.com/shinriyo))

## [v0.5.0](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.5.0) (2015-01-05)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.4.3...v0.5.0)

**Implemented enhancements:**

- Close room from server side [\#84](https://github.com/miguelgrinberg/Flask-SocketIO/issues/84)
- Failed to Debug under WingIDE for setting “app.debug = True” [\#59](https://github.com/miguelgrinberg/Flask-SocketIO/issues/59)

**Fixed bugs:**

- Running in debug mode requires monkey patching [\#66](https://github.com/miguelgrinberg/Flask-SocketIO/issues/66)
- gracefull error handling for missing arguments from client [\#21](https://github.com/miguelgrinberg/Flask-SocketIO/issues/21)

**Closed issues:**

- Change resource from '/socket.io' to other [\#80](https://github.com/miguelgrinberg/Flask-SocketIO/issues/80)

## [v0.4.3](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.4.3) (2014-12-16)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.4.2...v0.4.3)

**Merged pull requests:**

- Fix typo on front doc page [\#77](https://github.com/miguelgrinberg/Flask-SocketIO/pull/77) ([andrejsc](https://github.com/andrejsc))

## [v0.4.2](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.4.2) (2014-11-30)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.4.1...v0.4.2)

**Closed issues:**

- Client calls disconnect method are a few seconds of inactivity [\#70](https://github.com/miguelgrinberg/Flask-SocketIO/issues/70)
- Installation not working. No module named flask.ext.socketio.SocketIO [\#69](https://github.com/miguelgrinberg/Flask-SocketIO/issues/69)
- greenlet.error: cannot switch to a different thread [\#65](https://github.com/miguelgrinberg/Flask-SocketIO/issues/65)
- broadcast before direct communication [\#63](https://github.com/miguelgrinberg/Flask-SocketIO/issues/63)
- SocketIO makes Celery worker hang [\#61](https://github.com/miguelgrinberg/Flask-SocketIO/issues/61)

## [v0.4.1](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.4.1) (2014-10-23)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.4.0...v0.4.1)

**Closed issues:**

- Get rid of monkey.patch\_all\(\) [\#55](https://github.com/miguelgrinberg/Flask-SocketIO/issues/55)
- RuntimeError: You need to use a gevent-socketio server. [\#39](https://github.com/miguelgrinberg/Flask-SocketIO/issues/39)

## [v0.4.0](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.4.0) (2014-09-23)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.3.8...v0.4.0)

**Closed issues:**

-  'base64Encoding' is deprecated: first deprecated in iOS 7.0 [\#54](https://github.com/miguelgrinberg/Flask-SocketIO/issues/54)
- Sessions? [\#48](https://github.com/miguelgrinberg/Flask-SocketIO/issues/48)
- Disconnect a client [\#46](https://github.com/miguelgrinberg/Flask-SocketIO/issues/46)
- missing module socketio [\#45](https://github.com/miguelgrinberg/Flask-SocketIO/issues/45)
- error: no handlers could be found for logger 'socketio.virtsocket' [\#42](https://github.com/miguelgrinberg/Flask-SocketIO/issues/42)

**Merged pull requests:**

- Add optional exception handler [\#50](https://github.com/miguelgrinberg/Flask-SocketIO/pull/50) ([alanhdu](https://github.com/alanhdu))

## [v0.3.8](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.3.8) (2014-06-15)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.3.7...v0.3.8)

**Closed issues:**

- Broadcast does not work with gunicorn [\#37](https://github.com/miguelgrinberg/Flask-SocketIO/issues/37)
- uwsgi deployment [\#36](https://github.com/miguelgrinberg/Flask-SocketIO/issues/36)
- SocketIO seems to be not working with multiple workers in gunicorn [\#35](https://github.com/miguelgrinberg/Flask-SocketIO/issues/35)
- is Flask-SocketIO working with socketio 1.0? [\#34](https://github.com/miguelgrinberg/Flask-SocketIO/issues/34)
- Runtime Error [\#33](https://github.com/miguelgrinberg/Flask-SocketIO/issues/33)
- Session context from within socketio.on wrapper is not persisted [\#30](https://github.com/miguelgrinberg/Flask-SocketIO/issues/30)
- Problem with server-generated events in gunicorn [\#28](https://github.com/miguelgrinberg/Flask-SocketIO/issues/28)
- Working Behind an \(NginX\) Proxy? [\#22](https://github.com/miguelgrinberg/Flask-SocketIO/issues/22)

## [v0.3.7](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.3.7) (2014-05-21)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.3.6...v0.3.7)

**Closed issues:**

- App runner does not log server's IP/port to console? [\#31](https://github.com/miguelgrinberg/Flask-SocketIO/issues/31)

## [v0.3.6](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.3.6) (2014-05-13)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.3.5...v0.3.6)

**Closed issues:**

- Keyerror [\#26](https://github.com/miguelgrinberg/Flask-SocketIO/issues/26)

## [v0.3.5](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.3.5) (2014-05-07)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.3.4...v0.3.5)

**Closed issues:**

- Error with Heroku [\#24](https://github.com/miguelgrinberg/Flask-SocketIO/issues/24)
- Error when terminating application [\#23](https://github.com/miguelgrinberg/Flask-SocketIO/issues/23)

## [v0.3.4](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.3.4) (2014-04-27)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.3.3...v0.3.4)

**Fixed bugs:**

- Unable to send on global namespace [\#18](https://github.com/miguelgrinberg/Flask-SocketIO/issues/18)

**Merged pull requests:**

- Correct URL to socket.io.min.js [\#17](https://github.com/miguelgrinberg/Flask-SocketIO/pull/17) ([mozz100](https://github.com/mozz100))

## [v0.3.3](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.3.3) (2014-04-22)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.3.2...v0.3.3)

**Closed issues:**

- Emit failing to serialize SQLAlchemy models  [\#19](https://github.com/miguelgrinberg/Flask-SocketIO/issues/19)
- Broken with gunicorn [\#16](https://github.com/miguelgrinberg/Flask-SocketIO/issues/16)

## [v0.3.2](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.3.2) (2014-03-31)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.3.1...v0.3.2)

**Closed issues:**

- server-generated broadcast messages fail when using gunicorn [\#14](https://github.com/miguelgrinberg/Flask-SocketIO/issues/14)

## [v0.3.1](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.3.1) (2014-03-24)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.3.0...v0.3.1)

**Closed issues:**

- Server Push Example [\#12](https://github.com/miguelgrinberg/Flask-SocketIO/issues/12)
- dynamic namespacing [\#5](https://github.com/miguelgrinberg/Flask-SocketIO/issues/5)
- Spawning a broadcast [\#3](https://github.com/miguelgrinberg/Flask-SocketIO/issues/3)
- Add testing methods/examples [\#1](https://github.com/miguelgrinberg/Flask-SocketIO/issues/1)

**Merged pull requests:**

- Allow SocketIOServer keywords to get passed through [\#13](https://github.com/miguelgrinberg/Flask-SocketIO/pull/13) ([shepwalker](https://github.com/shepwalker))

## [v0.3.0](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.3.0) (2014-03-08)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.2.2...v0.3.0)

## [v0.2.2](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.2.2) (2014-02-19)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.2.1...v0.2.2)

**Closed issues:**

- No ability to respond to client requested ack [\#9](https://github.com/miguelgrinberg/Flask-SocketIO/issues/9)
- Send message to speciffic connections [\#8](https://github.com/miguelgrinberg/Flask-SocketIO/issues/8)
- can not use it with celery. [\#2](https://github.com/miguelgrinberg/Flask-SocketIO/issues/2)

**Merged pull requests:**

- Fix client requested ack issue [\#11](https://github.com/miguelgrinberg/Flask-SocketIO/pull/11) ([TronPaul](https://github.com/TronPaul))
- Add sessid to TestSocket [\#10](https://github.com/miguelgrinberg/Flask-SocketIO/pull/10) ([TronPaul](https://github.com/TronPaul))

## [v0.2.1](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.2.1) (2014-02-15)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.2.0...v0.2.1)

## [v0.2.0](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.2.0) (2014-02-13)
[Full Changelog](https://github.com/miguelgrinberg/Flask-SocketIO/compare/v0.1.0...v0.2.0)

**Merged pull requests:**

- Werkzeug debugger support [\#4](https://github.com/miguelgrinberg/Flask-SocketIO/pull/4) ([noirbizarre](https://github.com/noirbizarre))

## [v0.1.0](https://github.com/miguelgrinberg/Flask-SocketIO/tree/v0.1.0) (2014-02-10)


\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*