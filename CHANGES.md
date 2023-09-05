# Flask-SocketIO change log

**Release 5.3.6** - 2023-09-05

- Fixes in the test client to support recent changes in Socket.IO dependencies [#2006](https://github.com/miguelgrinberg/flask-socketio/issues/2006) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/08411f99014d3680f1e2591b1e9ff1c5bfd0a5f5))

**Release 5.3.5** - 2023-07-26

- Prevent `allow_unsafe_werkzeug` option from being passed to web servers [#2001](https://github.com/miguelgrinberg/flask-socketio/issues/2001) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/d6c6b8c336f533a9bac50cf3d7dbcc51669209b2))

**Release 5.3.4** - 2023-05-03

- Fixed cookie handling in Test Client for Flask >= 2.3 [#1982](https://github.com/miguelgrinberg/flask-socketio/issues/1982) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/70203246bcbc23715350ca5505527b31bf0693c1))
- Correctly handle ConnectionRefusedError in connect handler [#1959](https://github.com/miguelgrinberg/flask-socketio/issues/1959) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/64a18263cd3b864a5bb5b25bb5901350b8c1264d))
- More secure nginx configuration examples [#1966](https://github.com/miguelgrinberg/flask-socketio/issues/1966) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9b861ceaa91bbe168376cf5cdac6c2917e448946)) (thanks **Lorenzo Leonardini**!)

**Release 5.3.3** - 2023-03-17

- Invalid arguments passed in `call()` function [#1953](https://github.com/miguelgrinberg/flask-socketio/issues/1953) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/d2cf0491e5cbadfa0bab626c77d745dbb647236f))

**Release 5.3.2** - 2022-11-20

- Deliver callbacks from different namespaces [#1909](https://github.com/miguelgrinberg/flask-socketio/issues/1909) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/94240a4af3cef03354810bef0a35b848c2e16a28))
- Fix documentation typos [#1881](https://github.com/miguelgrinberg/flask-socketio/issues/1881) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/94692d365ce328986d7b802d6177decf8ba86ac6)) (thanks **Tim Gates**!)

**Release 5.3.1** - 2022-09-11

- Always pop `allow_unsafe_werkzeug` option from kwargs [#1877](https://github.com/miguelgrinberg/flask-socketio/issues/1877) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9923502960da2c543c43bcc498d6acc2fc80179c)) (thanks **zakx**!)

**Release 5.3.0** - 2022-08-23

- Add `call()` function to emit to the client and wait for the callback response [#1830](https://github.com/miguelgrinberg/flask-socketio/issues/1830) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/94a28590e211784e9365ac21185fd617bd1a0a9f))
- Manage each test client's connection state independently [#1829](https://github.com/miguelgrinberg/flask-socketio/issues/1829) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/196c50f1085557af59c89bcf9b927144786d99e1))
- Support new Flask 2.2 session structure [#1856](https://github.com/miguelgrinberg/flask-socketio/issues/1856) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/6f270eef955e28289285c03138187511bc148547))
- Do not allow Werkzeug to be used in production by default [#1814](https://github.com/miguelgrinberg/flask-socketio/issues/1814) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/e35a0f4a69c343412cdfb879e7545707f933934a))
- Fix documentation typo [#1857](https://github.com/miguelgrinberg/flask-socketio/issues/1857) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/33436dc2c7e9b8c003186be66031d49bf40de564)) (thanks **Vincent Kuhlmann**!)

**Release 5.2.0** - 2022-05-22

- Better handling of `message_queue` connection argument [#1130](https://github.com/miguelgrinberg/flask-socketio/issues/1130) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/2afebb95be724ad62431ec91040f6d365a8fc969))
- More robust handling of `to` and `room` arguments of `emit` and `send` [#1771](https://github.com/miguelgrinberg/flask-socketio/issues/1771) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/f7ca69af129e6575f82142f27fbf9054522e969d))

**Release 5.1.2** - 2022-04-24

- No need to push a new app context in the test client [#1669](https://github.com/miguelgrinberg/flask-socketio/issues/1669) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/bd6a0e2acbaff83822d35025bdbf8984d02fb88b))
- Remove 3.6 and pypy-3.6 builds, add 3.10 and pypy-3.8 ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/004d34482f42f168b087d966bc414c5b1c7e9da0))
- Improve documentation on `start_background_task()` function ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a10ea5cf65007061d7b3fd87b530c382007adebb))
- changed `room` argument to `to` in documentation examples [#1665](https://github.com/miguelgrinberg/flask-socketio/issues/1665) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/086196a88781f58ca6e13f476c1cdf8129e1e15c)) (thanks **David McInnis**!)
- Fix documentation typo [#1793](https://github.com/miguelgrinberg/flask-socketio/issues/1793) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/732d223b053ac66b1be7a41abf9824c7e1e895ff)) (thanks **Gabe Rust**!)
- Fix example code in documentation [#1787](https://github.com/miguelgrinberg/flask-socketio/issues/1787) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/da37fce56379f37b41102f4ccaf2b315b27b4459)) (thanks **Louis-Justin TALLOT**!)

**Release 5.1.1** - 2021-08-02

- Only use SSL socket if at least one SSL kwarg is not None [#1639](https://github.com/miguelgrinberg/flask-socketio/issues/1639) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/57e525f6b9ac46c83004f8070ef55c943097a293)) (thanks **JT Raber**!)
- Remove unused SSL arguments from eventlet server options [#1639](https://github.com/miguelgrinberg/flask-socketio/issues/1639) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/4b5e5202b51b672677841c12296451fe11d9cc52))
- Remove executable permissions from files that lack shebang lines [#1621](https://github.com/miguelgrinberg/flask-socketio/issues/1621) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/ee2c4e9b50b159fd258497cd52bbe27342dc4089)) (thanks **Ben Beasley**!)
- Improved project structure ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/df04df439535ad5eb7ce910ae1e8204aed3cabfc))

**Release 5.1.0** - 2021-05-28

- Add reloader_options argument to socketio.run[#1556](https://github.com/miguelgrinberg/flask-socketio/issues/1556) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/f9036ebd6fa8301aecbbbafd79087523e83d18a1))
- Pass auth data from client in connect event handler [#1555](https://github.com/miguelgrinberg/flask-socketio/issues/1555) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/43dc6e57e9a243065a0d1f1d51fe8257ab51d7c2))
- Do not show simple-websocket install prompt if it is already installed ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/03a52c8df48c6d1340107c57d7a99d1357df9ac3))
- Fix namespace bug in example [#1543](https://github.com/miguelgrinberg/flask-socketio/issues/1543) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/acc57aff7f5e6b322adfe7600b5177c74e7b54ef))
- Added index to documentation [#724](https://github.com/miguelgrinberg/flask-socketio/issues/724) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/f839a4cbe24644500efad287cce24c38a058a36c))
- Fixed typo in documentation [#1551](https://github.com/miguelgrinberg/flask-socketio/issues/1551) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/22a7ea42ed771100c347d52762e38e719b373a0f)) (thanks **Mayank Anuragi**!)

**Release 5.0.3** - 2021-05-15

- Document the use of simple-websocket with the development web server ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/6a2463cc21e56dfac27f63832d2510a3e1467634))
- Show transport in example apps ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/044e9c066c53c865abb1eee0e81c90a0c7022b7e))
- Added Open Collective funding option ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/ab99680cefba577b06b19227480511ad6508a1d4))

**Release 5.0.2** - 2021-05-14

- Silence deprecation warning from Werkzeug 2.x [#1549](https://github.com/miguelgrinberg/flask-socketio/issues/1549) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/6563634e4c7836479ff5d38d20f4339e6bcf92ab))
- Updated server options in documentation ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/6bcd1dc29d1dde4f61e582fc62f4bb752008615e))
- Updated socketio javascript client versions in documentation ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/c527c90cbe2b6f141ca94ec75964af5d0e304ab7))
- Fix typo in documentation [#1524](https://github.com/miguelgrinberg/flask-socketio/issues/1524) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/2f1c322e687a8f7f080a081f042efdc6c8532123)) (thanks **lennertcl**!)
- Change room documentation from room= to to= [#1519](https://github.com/miguelgrinberg/flask-socketio/issues/1519) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/b33cab093c85d4888093a9c2992eb8a815695b4d)) (thanks **David McInnis**!)
- Fixed a type in the Kafka URL in the documentation [#1476](https://github.com/miguelgrinberg/flask-socketio/issues/1476) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a222638186f57980a08d2d4e98624dd27c1e2bd3)) (thanks **VVakko**!)
- Fixed typos in documentation [#1447](https://github.com/miguelgrinberg/flask-socketio/issues/1447) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/3f7ef81fee05be6b674521bd5850676bb2021897))

**Release 5.0.1** - 2020-12-19

- Fix handling of  argument [#1441](https://github.com/miguelgrinberg/flask-socketio/issues/1441) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/4ec274831551a3141a5838d9fd4c5e983f637a3a))
- Add python-engineio to version compatibility table ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/2934b469da80c1f5df9f560f06cf11e61dd2f1bd))
- Test client: pass packets through an encode/decode cycle [#1427](https://github.com/miguelgrinberg/flask-socketio/issues/1427) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/ffe66fee0e72737aa974337a3ceaab4553ab3325))

**Release 5.0.0** - 2020-12-13

- Move to python-socketio 5.x and the 3.x JavaScript releases ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/0c674b89c094f1085ad05fd7b6d2c304b9cf5791))
  - Also see [python-socketio change log](https://github.com/miguelgrinberg/python-socketio/blob/master/CHANGES.md)
  - Also see [python-engineio change log](https://github.com/miguelgrinberg/python-engineio/blob/master/CHANGES.md)
- add @socketio.event convenience decorator ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/62717a852983bbf5d89d9b8f898282712c9bbf24))
- Rename `room`  argument to `to` ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/4c69c9a807a94120c4a07274e29ef9b9a41bfb86))
- Documentation updates ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/e864441e7ac7263d77e9a2e18863ebc22dcbf6ec)) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/c91244a30e77104c6df827b55f9dfad8ae9c7788))

**Release 4.3.2** - 2020-11-30

- Only use python-socketio 4.x versions as dependencies for now ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/59740d3eb50395f44cfb786b85215b4ec9b795e9))
- Added troubleshooting section to the documentation ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/27b148b6b614c916f2b3417e6d160a6456335e66))
- Fixed incorrect use of `has_request_context` [#1324](https://github.com/miguelgrinberg/flask-socketio/issues/1324): [#1325](https://github.com/miguelgrinberg/flask-socketio/issues/1325) - Added proper call to has_request_context function Co-authored-by: igor_kantorski <igor.kantorski@globedata.pl> ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9a53243eae1a1289f670ce8f8941e9867a9de531)) (thanks **igoras1993**!)
- Move builds to GitHub actions ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/46cfcbf61fe63e8243cfb0db1b6273356d419f47))

**Release 4.3.1** - 2020-07-02

- fix is_connected in test client ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/0d2f041dc0e7cd976860c2d2c9fb163bd20f5460))

**Release 4.3.0** - 2020-04-20

- Handle callbacks for emits outside of request context [#1054](https://github.com/miguelgrinberg/flask-socketio/issues/1054) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/1bd15e05b75aaf94dacd4f24af44601b76d300a9))
- Improve test client unit test to use two concurrent clients ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/2c6b07d0419f2b6e03554c32e42a91cf963c6d6d))
- Accept skip_sid argument in emit[#1147](https://github.com/miguelgrinberg/flask-socketio/issues/1147) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/c06e78e78de3d10f9009bf778ad188bf3f4945ed))
- Fix is_connected() method in test client (Fixes https://github.com/miguelgrinberg/python-socketio/issues/385) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a05ff51344654aef00b8dc0fce8028500d380b05))
- Log warning when gevent is used but WebSocket is missing [#1140](https://github.com/miguelgrinberg/flask-socketio/issues/1140) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/15ad45a6b90362bc1b73b6a7b0fa6781c6b98b05)) (thanks **Eric Rodrigues Pires**!)
- More accurate logging documentation ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/255d3d6b41b4f22736d2798a8f70264334eb3173))

**Release 4.2.1** - 2019-08-05

- Add support for Apache Kafka message queue [#700](https://github.com/miguelgrinberg/flask-socketio/issues/700) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/f20268a3ec14af3e8d6681c2ffd01e299dc4f6df)) (thanks **Vincent Mézino**!)
- Update CORS documentation ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/d9cd34a86dedf96ca5232cf981b54b4c1c6e362d))

**Release 4.2.0** - 2019-07-29

- Address potential websocket cross-origin attacks [#128](https://github.com/miguelgrinberg/python-engineio/issues/128) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/7548f704a0a3000b7ac8a6c88796c4ae58aa9c37))
- Documentation for the Same Origin security policy ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/42d4e02055f5936f1322982bf44a845987d75144))

**Release 4.1.1** - 2019-07-29

- Fix typo in "Using nginx" section [#1007](https://github.com/miguelgrinberg/flask-socketio/issues/1007) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9e152b24ec30dd712886c4da3ec6a3aded855a00)) (thanks **Steffen Schneider**!)
- updated python-socketio min version requirement to 4.0.0 [#1006](https://github.com/miguelgrinberg/flask-socketio/issues/1006) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/40a34c119a6b7f7e00d2a476d26e985cbd10ec19)) (thanks **Shantanu Hazari**!)

**Release 4.1.0** - 2019-06-09

- Add ConnectionRefusedError exception from python-socketio [#989](https://github.com/miguelgrinberg/flask-socketio/issues/989) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/3f9fda8f0de551567834400ff72a95c10c7d42b4))
- Invoke Socket.IO callbacks with app and request context [#262](https://github.com/miguelgrinberg/flask-socketio/issues/262) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/75a75d47cb20fca8a8b2b2818a7602d43b4cea1f))
- Copy handler's name and docstring to handler wrapper [#573](https://github.com/miguelgrinberg/flask-socketio/issues/573) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/4e0329b59e653edc19b31f05823b47bd63c0bc72))
- Less aggressive monkey patching for gevent [#413](https://github.com/miguelgrinberg/flask-socketio/issues/413) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/55d02d97708bd91b7d8f761ab57aba8d946039ff))
- Updates jquery and socket.io in example application [#988](https://github.com/miguelgrinberg/flask-socketio/issues/988) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/67da0d6627149c27da4ddc9b675aacf946dc3588)) (thanks **sillyfrog**!)

**Release 4.0.0** - 2019-05-19

- move to the latest python-socketio 4.x releases ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/686abcaf69c27f6fb6084d0948832ffff8177755))
- SocketIOTestClient can handle disconnect event from server [#967](https://github.com/miguelgrinberg/flask-socketio/issues/967) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/611fa68e102b7b49ac77d48406a034f23aca4998)) (thanks **Jack**!)
- example app: disconnect in callback function [#453](https://github.com/miguelgrinberg/flask-socketio/issues/453) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/f8ee01f938afcd13d4cae282976946660db8e982))
- update documentation for skip_sid argument supporting lists ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/932b0296afea789f51c0b7f39f99a561593fb257))
- add /static block to nginx configuration example [#222](https://github.com/miguelgrinberg/flask-socketio/issues/222) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/e052ae6d7b865929bfb7dca4b936902d204ccdb6))
- add notes on monkey patching [#383](https://github.com/miguelgrinberg/flask-socketio/issues/383) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/5dd2bca681cc826fa60558ec244633437bfebaf4))
- note the event names that are reserved in the documentation ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/0c9d1b32499ca5091cf04833c32f3ade803be6e7))
- minor doc improvements [#960](https://github.com/miguelgrinberg/flask-socketio/issues/960) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a0c29a94b1d53306550e8c5ffc4fcb71f6fb20b7))
- updated some requirements ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/4bef800d5e7ba7d98a6f4cd94191ff0b4496c334))
- add link to stack overflow for questions ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/db46f062b2d13c7c464f625d5e1976d9625a0f37))
- helper release script ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/1fd43a3fc86be8848fc6d70d80638db688f4eb97))

**Release 3.3.2** - 2019-03-09

- update dependencies ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/b65e92b0b97bcbe2f047d508ed520cecd9765f32))

**Release 3.3.1** - 2019-02-16

- keep connected status in test client ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/5e399d544317a741234d3260c04aca4ba2e18e5a))

**Release 3.3.0** - 2019-02-16

- added flask_test_client option to Socket.IO test client ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/074278808e9a732f5f9fcb9273a312fbb6e279bd))

**Release 3.2.2** - 2019-02-12

- suppress web server warning when in write-only mode ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/ca582618863070657f0565d614552a7f65c9fb6d))

**Release 3.2.1** - 2019-01-24

- remove error about eventlet/gevent used with flask run ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9a717733a1a1a93c155d8b41402a5b5527b6eee1))

**Release 3.2.0** - 2019-01-23

- discontinue the customized flask run command ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9bde4beda523d539e2113151e8c4d3f88765a5ea))
- spelling corrected [#869](https://github.com/miguelgrinberg/flask-socketio/issues/869) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/afbd83ef75ed948bc5814c668b73f1be9573f0e4)) (thanks **Muhammad Hamza**!)

**Release 3.1.2** - 2018-12-21

- make unit tests compatible with Python 3.7.1 ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/f84a7dfbe34110dc604a7e2df9098e4348248d55))

**Release 3.1.1** - 2018-12-08

- fix dependency version ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/65f29ce16e386d5a0718de7e78ce39a77bd732d6))

**Release 3.1.0** - 2018-11-26

- move to the new WSGIApp class in python-socketio ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/db74fa385e9f508fff25029f2a3bfd1b86916960))
- remove misleading target keyword arg in examples ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/7463d340581bff18be09b989ab938d367e2cf408))
- Fix test client [call]back returning [#732](https://github.com/miguelgrinberg/flask-socketio/issues/732) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/4b0648cb195be3f94344d9b0b7f77d9b312256d8)) (thanks **Alex Pilon**!)

**Release 3.0.2** - 2018-09-12

- undoing fix for [#713](https://github.com/miguelgrinberg/flask-socketio/issues/713) as it breaks the reloader for regular apps ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/b20224b968fd99ee69e3cefc78d07e989c833064))
- README.md: Add syntax highlighting to python code [#723](https://github.com/miguelgrinberg/flask-socketio/issues/723) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/cc49b24b1aabcfe976dc402f798717939664e378)) (thanks **Meet Mangukiya**!)
- Fix typo in docs [#717](https://github.com/miguelgrinberg/flask-socketio/issues/717) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/cec3986a5ba05f84df4894eeeb715d5c1a290abf)) (thanks **Grey Li**!)

**Release 3.0.1** - 2018-06-03

- reloader fix [#713](https://github.com/miguelgrinberg/flask-socketio/issues/713) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/549cad6307c066c24146590a5c3427fa4b9a8fa3))

**Release 3.0.0** - 2018-04-30

- minor fix for Flask 1.0 ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/39649c83393da5b69d26e5e410a49c86af71a0f9))
- add pypy3 target to travis builds ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9d4a5a46edc359ceda873f3f984216946a8051c2))
- remove outdated warning about gunicorn R19 [#563](https://github.com/miguelgrinberg/flask-socketio/issues/563) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a917674006932088eea46311886d3e8c44d5984a))
- improved documentation for disconnect() [#673](https://github.com/miguelgrinberg/flask-socketio/issues/673) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/73f17fa3d24122ea4ece098a3c9bdb1898024eeb))

**Release 2.9.6** - 2018-03-10

- support --with[#659](https://github.com/miguelgrinberg/flask-socketio/issues/659) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/f08cc232fc1313c2d8a423d78a6444c127d116ae)) (thanks **Kareem Zidane**!)
- add optional namespace argument to disconnect function ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9cfa8e117129841e8f060ca53f412985a65d4f54))

**Release 2.9.5** - 2018-03-09

- add optional sid argument to disconnect function ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/ff9f385bfed394c026fd9bb69e7ec803e0c53b5f))
- Fix typo in index.rst [#650](https://github.com/miguelgrinberg/flask-socketio/issues/650) Fix typographical error in the Authentication section of the file. ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/8d64c781eb7c5d51103ef766a6cc5ab2af08dc77)) (thanks **Michael Obi**!)

**Release 2.9.4** - 2018-02-25

- make managed session more like a real session ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/fdf8edbfdeaaf909bb59b1dc86822f27aa06df2d))
- Update docs link [#613](https://github.com/miguelgrinberg/flask-socketio/issues/613) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/4d1c3cc29990226a85ba0f05d811043b42d0b1d9)) (thanks **Grey Li**!)

**Release 2.9.3** - 2017-12-11

- Support binary data in the test client [#601](https://github.com/miguelgrinberg/flask-socketio/issues/601) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/ad0001dc04dc37f439bd52b82b02fc15434b38b8))
- Update docs now gevent-websocket is available for python3 [#599](https://github.com/miguelgrinberg/flask-socketio/issues/599) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/96cf8ee275fb3fd2e25c9dd1490d850ec0044c6d)) (thanks **Andrew Burrows**!)
- fix param name in doc string [#585](https://github.com/miguelgrinberg/flask-socketio/issues/585) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/84da99af88b537e68ec3862017a8b48ca68f810d)) (thanks **Grey Li**!)
- Add missing json argument in send[#587](https://github.com/miguelgrinberg/flask-socketio/issues/587) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/07284632727429e2cc174d68bad641f9060769e9)) (thanks **Grey Li**!)
- improved documentation on acknowledgements ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/e5a4bfd33cbff1e5c2f39d1588e0e71abc4745e7))
- Support Redis SSL connection string [#569](https://github.com/miguelgrinberg/flask-socketio/issues/569) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/20d766d34672cfbae65f908231bd2338ee8643e3)) (thanks **Ján Koščo**!)
- updated requirements [#534](https://github.com/miguelgrinberg/flask-socketio/issues/534) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/466bbc3be7e53025f24ea45d3f68b9db332393d6))
- prevent race conditions with thread start [#493](https://github.com/miguelgrinberg/flask-socketio/issues/493) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/5c7d14bd602475c2b4a5be618badb3b00c96cc3c))
- Documented some protocol defaults. [#516](https://github.com/miguelgrinberg/flask-socketio/issues/516) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/61c179d337428224b58f7c062b139db3df843152))

**Release 2.9.2** - 2017-08-05

- some more unit tests ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/50ab42a3705bb03182735c70f83d81020b2037e1))
- Support custom headers and query string in test client [#520](https://github.com/miguelgrinberg/flask-socketio/issues/520) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/ecf5925827a916ef52361856290f16087c4e36e9))
- added **kwarg to  pywsgi.WSGIServer when import WebSocketHandler failed [#518](https://github.com/miguelgrinberg/flask-socketio/issues/518) there is any reason to not pass **kwarg pywsgi.WSGIServer in the case WebSocketHandler fail to import? ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/8a09692873ed6dea35599be7f1f607e1aa58170f)) (thanks **simus81**!)

**Release 2.9.1** - 2017-07-16

- also add ignore_queue to send function ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/1d37649fbdcfd15b98cadc524580f6d4d8d80bb6))
- expose ignore_queue param in the emit method [#505](https://github.com/miguelgrinberg/flask-socketio/issues/505) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/00a8de06d0cbc2051412729ad050669aef2085f2)) (thanks **hsvlz**!)

**Release 2.9.0** - 2017-06-26

- added flask-login to sessions example ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a51a3ba688c27b5d0294268d8fece6f79806bd02))
- updated example requirements file ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/ece16238c91349585dce144038d2af0f807ef2af))
- better support for user sessions ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/742c5ba23e53b5bdaf0530ed483dd808e50dca08))
- remove unused code related to previous commit ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/3924544e0e6db77cee8bc9d461ab825be9606738))
- Support beaker (and possibly other) sessions ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/2625426499e3b375336ef78244b5df5571c2c57f))
- Fix typo in top level doc [#452](https://github.com/miguelgrinberg/flask-socketio/issues/452) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/8d3d72952456662352e3e54ecb006a7e36238b2f)) (thanks **Ben Harack**!)
- Added an optional IPv6 support in eventlet ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/d050d688bcdd7f99550d8a26138896b58a081191)) (thanks **Pavel Pushkarev**!)
- fix KeyError ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/31e06d4472b27dbbac91f03319e53d46d8130b07))
- cleanup previous merge ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/5d432c784b19532171ef2dd6334b4e802d41eb8c))
- Fix 'path' or 'resource' doesn't work. ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a1d771940ba11b9802684c53f6bd34e6d2819170)) (thanks **Water Zheng**!)

**Release 2.8.6** - 2017-03-21

- add documentation for [#433](https://github.com/miguelgrinberg/flask-socketio/issues/433) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/3dac05157f75c84ed016230a32463f1bbc16cdcf))
- specify namespace in room related functions ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a41e6cb7766b8807a05a723edc279c3c39f5367a)) (thanks **Samuel Kortchmar**!)

**Release 2.8.5** - 2017-03-02

- specify sid in room related functions [#420](https://github.com/miguelgrinberg/flask-socketio/issues/420) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/6a3462d726be38b463361f681f01a78a5d771153))

**Release 2.8.4** - 2017-02-17

- allow @socket.on decorators to be chained [#408](https://github.com/miguelgrinberg/flask-socketio/issues/408) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/4a01d816e411f31b445b876ee2b0b8ac57502ef6))
- add 3.6 builds, remove 3.3 ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/32affb9d1ba6f15e445ad876cb9cd2f3c60538f1))

**Release 2.8.3** - 2017-02-13

- updated test client to work with latest python-socketio release [#405](https://github.com/miguelgrinberg/flask-socketio/issues/405) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/6d5fba300f032613fdfc1315edf784da83b153ea))
- add support for using zmq as the message queue transport ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/4ee08fffdbb87a78681b00bcb3d40d0dcee3baae)) (thanks **Eric Seidler**!)
- Fix a typo [#400](https://github.com/miguelgrinberg/flask-socketio/issues/400) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/551f81e80cad85b7cdcb1ff4d38dffe412fdc6bd)) (thanks **Jordan Suchow**!)

**Release 2.8.2** - 2016-12-16

- make a copy of the environ dict ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/be088580f94d1528ead53ea8c3784ca76da5ecff))

**Release 2.8.1** - 2016-11-27

- Do not call init_app when an app or message_queue aren't given [#367](https://github.com/miguelgrinberg/flask-socketio/issues/367) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/37279e270547293ac284dbedc53b90d24bd978db))
- Improved nginx section of the documentation [#334](https://github.com/miguelgrinberg/flask-socketio/issues/334) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/2f7790c6538bf9de0cb795ad2cedba9cc1304aa7))

**Release 2.8.0** - 2016-11-26

- Pass client manager specific arguments in emit and send calls ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/10426ddf4e1e9fd8192f9636da32c471d9de4856))
- Support for "skip_sid" option. [#365](https://github.com/miguelgrinberg/flask-socketio/issues/365) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a8ae4791af0a573e83c48a19686aae107498ebd4))
- Make sure the test client is not used with a message queue [#366](https://github.com/miguelgrinberg/flask-socketio/issues/366) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/e14e5de75b617271de75a1a964702bdf48e4c814))
- Update custom namespace doc example [#364](https://github.com/miguelgrinberg/flask-socketio/issues/364) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/c1ba02cf52891b161bfc85e4b7f8e082aea77fd3)) (thanks **LikeMyBread**!)

**Release 2.7.2** - 2016-11-04

- Use standard run command if flask-socketio isn't instantiated [#347](https://github.com/miguelgrinberg/flask-socketio/issues/347) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/7af6740b8332e65b49b065ab458a1deec73f0b2f))
- Improve socketio connect function in example for http[s] ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/391e793153dfee861795693ad5bdefb6d1367c33)) (thanks **Kyle Lawlor**!)
- preserve options given in constructor when init_app is called [#321](https://github.com/miguelgrinberg/flask-socketio/issues/321) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/f97673980f28cb3c809763e949aa1e20ddff21cc))
- include license and readme in the package [#326](https://github.com/miguelgrinberg/flask-socketio/issues/326) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/032a28103617e264f0ceff27ec3125696b2c24ab))

**Release 2.7.1** - 2016-09-04

- add `__version__` to package ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/200424160e1f28b40e82daa5e427d8953614d612))

**Release 2.7.0** - 2016-09-01

- uwsgi support, class-based namespaces ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a009636020417eb2f8be83c99a7bca6050c57353))
- fix failing unit test ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/78b884cd73a0114db4f95f166bc5c90195653b6e))
- Add on_event(), the non-decorator version of on() ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/39f8795e8118a01596f74e3e34df8c9ddd93645b)) (thanks **Stefan Otte**!)
- improved callback handling on test client ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/6077d7a22a9460b58464e6ccd8e0d185310da6cc))
- add explicit eventlet.wsgi import [#309](https://github.com/miguelgrinberg/flask-socketio/issues/309) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/d604a7e854c31b20db0e01ed3c8baebd90642dd9))
- fix document typos: messaque -> message [#304](https://github.com/miguelgrinberg/flask-socketio/issues/304) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/4469cce5b77605effc76386a2811fd3524dbb262)) (thanks **朱✖️: (ง •_•)ง木犀**!)

**Release 2.6.2** - 2016-08-09

- ensure Flask's json is called with an app context [#297](https://github.com/miguelgrinberg/flask-socketio/issues/297) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/7aa06118e68f65f0b9e37030f008f93a76be6bb4))

**Release 2.6.1** - 2016-08-02

- Initialize received queue in test client [#295](https://github.com/miguelgrinberg/flask-socketio/issues/295) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/35399c57d0bc309220d20bcbf443c5483171ca1f))
- improved documentation on custom json encoder/decoder [#274](https://github.com/miguelgrinberg/flask-socketio/issues/274) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/6d4acee2dc324d43eedc063ea5807c38d0a3a0ea))

**Release 2.6** - 2016-07-24

- flask 0.11 cli support [#289](https://github.com/miguelgrinberg/flask-socketio/issues/289) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/91bc084de8c818e14d7ebb0894750f5657a65bf9))
- documentation for the test client class ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/b5cf4dfcedc2e5c7ec039f1a48f754a6375044d0))
- send should not require flask request ctx [#283](https://github.com/miguelgrinberg/flask-socketio/issues/283) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9ff7c392d43867ddce9b82a9d5e8ea2945708b43)) (thanks **yofreke**!)
- add path as an argument to Socket.IO, as an alias to resource ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/aa34521f35cedce2c9ff5e57a6dec82c7a9b1c81))

**Release 2.5** - 2016-06-28

- Improvements to example application ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9086588452078024d0ed2f9532de63bf16f5194f))
- expose async_mode, start_background_task and sleep from python-socketio ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/03dfe3344eaceb3db268d5a15332560d898f785f))

**release 2.4** - 2016-05-31

- more robustness in dealing with bad connections ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/5a1c70762a5f4e949fe8e2ddc7e209257281ad54))
- do not rause KeyError for unknown clients ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/82ffcfbd8e43d2a575b403ef2fae3f1d2ae19afc))

**Release 2.3** - 2016-05-15

- initialize client manager in test client ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/f999a70711c1812b2bbd69f270db46b04e639818))
- Switch to `flask_*` from deprecated `flask.ext.*` [#258](https://github.com/miguelgrinberg/flask-socketio/issues/258) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/76105fe1cfaf6419d431a76198ab901d3bfb977b)) (thanks **Jeff Widman**!)
- Fix typo in documentation Fix “ithreading” to “threading” ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/73932fdaf87defbadf3a9b3cf9a4905645a899de)) (thanks **whiteUnicorn**!)

**Release 2.2** - 2016-03-06

- Add notes regarding the need to monkey patch ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/21d6446000e6adc7e9c0488f8c4941ac7226e2aa))
- Added missing Python version classifiers to package ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/965b30a6dc83b570c05925ef9acee68ae57aadff))

**Release 2.1** - 2016-02-08

- Added reference of `_SocketIOMiddleware` instance to the SocketIO class ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/8c9c853eac93daecc41be0b0ad47611c4ca4f509)) (thanks **Grant**!)
- request context should not be needed when calling emit() with namespace [#213](https://github.com/miguelgrinberg/flask-socketio/issues/213) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/cfb7958e20466a6ed7fa44607585b5730a4c1e37)) (thanks **Tamas Nepusz**!)
- fixed a missed word in deployment docs [#210](https://github.com/miguelgrinberg/flask-socketio/issues/210) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/d528dc21a4e56106501af895e401a2542059a75c)) (thanks **George Lejnine**!)
- Documentation improvements on handling multiple arguments with tuples ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/000623e396ba7854ba58794735d6c5339f3ffdb4))
- Fix typo in documentation [#207](https://github.com/miguelgrinberg/flask-socketio/issues/207) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/d1a79a8e2207103969fa2550b3d0152f6e0b743d)) (thanks **Logan Chien**!)
- More documentation improvement and fixes ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a2a3c6296e7b37765db8cdb4cd716fa702faee9d))

**Release 2.0** - 2016-01-10

- Added documentation for uWSGI deployments ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/370628a1d9496701f0967e29dc5eb4f81871022f))
- support write_only flag for external processes ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/7d3c8ffb3d6d1270fd19cff04bf0e3bf7eb97122))
- Additional work and documentation for message queues ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/f9f54f922e1728897e42a037ac56facd12151f90))
- Added SSL enablement for eventlet ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/0618f75734e189f857fd644e500a1957092283dd)) (thanks **Chip Senkbeil**!)
- fixed ssl configuration issue fixed [#188](https://github.com/miguelgrinberg/flask-socketio/issues/188) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9cd254c5fdc45a2aa8f03ec372eddb2f74e8a7bb)) (thanks **muatik**!)
- message queue documentation ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/20f68f2298a6abb304f75b5f20b87af8180c5998))
- escaping of user provided input [#185](https://github.com/miguelgrinberg/flask-socketio/issues/185) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/68efeacd830ce07f8456df0478ad9a20e5399ab5))
- typo in __init__.py [#182](https://github.com/miguelgrinberg/flask-socketio/issues/182) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9831e77292ca44220a59efde56966fd909d839e5)) (thanks **Luke Yeager**!)
- Updated dependencies ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/4d50b84c01f7710e1b76e216c7eb85f70737f041))
- Integrate message queue backend ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/51b28409a58c1a57cd4f20be758e80d31e5451d9))
- Update index.rst Fix missprint ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a749af27d9cb0921e713431be75dffefed07d93f)) (thanks **Dmitry Zhuravlev-Nevsky**!)
- A few small documentation updates ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/11073c23622b3976d95dec50af85e119abe45a4d))
- Fix spelling mistake [#178](https://github.com/miguelgrinberg/flask-socketio/issues/178) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/faed71c0ceaf9dccebf08a7e7764ce3351ce5b5b)) (thanks **Liam Stanley**!)

**Release 1.2** - 2015-12-03

- Install the Werkzeug debugger middleware in the correct place ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/ed2eaeb6570bcafd0dec7eb8b5698dec3794fac0))
- Replace assertTrue with assertEqual where possible. ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/0018c072dfec51de821cb32b1179d7aa9eca5a60)) (thanks **jwg4**!)
- added python 3.5 to the build ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/02085f027c1b9e5964786ef355edc96e68c181b5))

**Release 1.1** - 2015-11-19

- recommend gunicorn 18 in documentation [#171](https://github.com/miguelgrinberg/flask-socketio/issues/171) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/b8f1a02026fbcc38ae3c8044606a91c3ad108600))
- Add installation instructions [#74](https://github.com/miguelgrinberg/flask-socketio/issues/74) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/07ef6110a913db9a1950a85580356729d2cae3a2))
- Minor documentation fixes ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/588406b6765c9869577c41727906186871ea5624))
- Add a close[#162](https://github.com/miguelgrinberg/flask-socketio/issues/162) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/cbfacad11f448e52fe6bfcf7472066da6f632297))
- exit with error if gevent-socketio is installed ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/f6610d3967817fef943960c9f6816b271387c344))

**Release 1.0** - 2015-10-29

- Merge branch 'v1.0' ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/d6baa817d06d805044f0e2ea2ab10a73c15fbfa9))
- daemonize background thread ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/89873a859aff3559bba2e6794c3f37beb42260b7))
- warn about performance when eventlet/gevent are not installed ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/6a3bb765d42120d03baa472b57da27195c7cf453))
- Reset async_mode to default ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/b935954b671665ea2b2354ce739cdaaad2050342))
- Fix socket.on decorator when using delayed app initialization ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/658945c5fd58913ee408945bea13a507d66901a7))

**Release 1.0b4** - 2015-10-18

- Do not fork the session unless it is modified ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/26172f41d889cd82860cfd76e39fc3b9e6d8b8db))
- Pass kwargs options to Werkzeug server ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/be900a87a70000974bebece3ada72e4a01cf83b8))
- Added section on upgrading from the 0.x releases ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/d92545088e47ee71885793fb25c6d50f348fba18))
- Avoid argument collisions in run() method ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/c2e21c65dff87f00c698e9f876f83849a6933672))
- Updated requirements ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/794fcb0ff224ec4ed24b8daa27ec082d167aea32))
- Removed old code that isn't needed anymore ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/1e2dc14cd04433f58542215641cbd2af33eb2c3d))
- Fix custom resource path. [#157](https://github.com/miguelgrinberg/flask-socketio/issues/157) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/dd0784897d7ab5d599ea164a3cd93bb44d0e6aca)) (thanks **Bekt**!)

**Release 1.0b3** - 2015-10-16

- automatically pick the best async_mode ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/81110ccbd40465acee0431a1ac711eccd05b1b29))
- Addressed additional problems with multi-application support ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/37316d7d1bf1453856956413505eeb72ef9c7296))

**Release 1.0b2** - 2015-10-15

- Allow more than one application per socketio instance [#146](https://github.com/miguelgrinberg/flask-socketio/issues/146) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/5f0dfbebfd3a8a8b9d94de3e5809efdaedf2f026))
- Moved server creation outside of socketio.run() ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/1f61ea0d175f8dfff71d4675e77698d4d5493e4f))
- added missing decorator return values [#149](https://github.com/miguelgrinberg/flask-socketio/issues/149) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/376a1327f528fad87647d3df7c9a44cb79f5dda2))
- documentation improvements ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/8284a2d6d84501f421eb01438e4bfab9df773a64))
- Support all async modes when app.debug is set ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/d79e27b640587e7f4a1cdcc0a9899f76ac22277c))

**Release v1.0b1** - 2015-09-20

- Replaced gevent, gevent-socketio and gevent-websocket with eventlet, python-socketio and python-engineio, gaining support for Python 3 and the latest versions of the Socket.IO Javascript client.
- Add include_self option to emit and send ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/ee77a52f206e7903c618695a17fa9ed235a9e1f0))
- Pass along extra_files param to run_with_reloader [#121](https://github.com/miguelgrinberg/flask-socketio/issues/121) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/096350a374a25cd1045328b6fc013238720a330b)) (thanks **bjamil**!)
- tests for ack ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/4ffd77145c033b5c142e34989edb63acd5e3823d)) (thanks **Patrick Jahns**!)
- return value from handler ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/db6b8ab50402ba4a404a3a49d0cb78ddd7758705)) (thanks **Patrick Jahns**!)
- Document how to use custom JSON encoder/decoder ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/7cf23c3b69e602d75af453e28335dad766c0bf83))
- Remove executable bit from regular files ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/7d8f8fbc11ec31ded91608a2895da57a57dad62c))
- Remove Python 2.6 from supported releases. ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/ac5b05a05007eb93594b9c62746548a0c1c56ce4))

**Release 0.6.0** - 2015-03-15

- Add event information in flask request variable [#101](https://github.com/miguelgrinberg/flask-socketio/issues/101) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a78432af5549f9b2e48c5f6f9fba31fce46debdc)) (thanks **Romain Paulus**!)
- Change README to reflect deprecated .ext import format [#98](https://github.com/miguelgrinberg/flask-socketio/issues/98) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/ba04c22c6f82b031264ba1c02b5a06825d2b5f56)) (thanks **Keyan Pishdadian**!)
- remove </div> tag it is html bug. So I removed. ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a7c702815f9eaf07ece1df43cb20af737c8cbefd)) (thanks **shinriyo**!)

**Release 0.5.0** - 2015-01-05

- close_room[#84](https://github.com/miguelgrinberg/flask-socketio/issues/84) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/558297da694f624cf5a8987a72eb2e3770dc0bca))
- added API section to docs ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/d8c7316759807ab3cd984fd059b71fdb49789d0f))
- add use_reloader option to socketio.run[#59](https://github.com/miguelgrinberg/flask-socketio/issues/59) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/760b61c533dc24bb2ae41e64d37690e5ec4fadeb))

**Release 0.4.3** - 2014-12-16

- allow clients to specify a custom socket.io resource name ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/3f6744f0692563494deea664eb6868fdd52a9b91))
- documentation improvements ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/6996e66bf9de9b1b5e9707c7637d31184dd2b4c2))
- Fix typo on front doc page [#77](https://github.com/miguelgrinberg/flask-socketio/issues/77) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/b017356ee2d4c59214e7b5cace42d263c520a79a)) (thanks **Andrejs Cainikovs**!)

**Release 0.4.2** - 2014-11-30

- use gevent monkey-patching when the reloader is enabled ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/2e7e050f13d1be23bd7c60c3192ae9107b67552c))

**Release 0.4.1** - 2014-10-23

- [#55](https://github.com/miguelgrinberg/flask-socketio/issues/55), no need to monkey patch ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/22d42481630fd2edfce46b445a42e42cbef2e0f4))

**Release 0.4** - 2014-09-23

- Add error handlers (on_error and on_default_error). ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/27c439574b779deca52b3af51be139d37e806d9a)) (thanks **Alan Du**!)
- Update index.rst fixed broken link to Flask-KVSession documentation. ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/4bd1f2a2d5aa03be00827692d99b969903a5d3df))

**Release 0.3.8** - 2014-06-15

- [#37](https://github.com/miguelgrinberg/flask-socketio/issues/37): broadcast without namespace ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9844dfe7a614257215e8c20919dcf2eb7afe3584))
- documented use of server-side sessions ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/2a08c09fc170945c2be9a4a790790a92c2967372))
- some more doc improvements ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/5fbaf8a78e0fc211bf0aeb001eb5ade204d37878))
- added client-side example code snippet ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/1bf7ed5c231b642844a184777a965b7b3269b659))
- documented the currently unsupported Socket.IO 1.x client library ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/db9342b195cc56e0b035982182413aead83da399))
- [#22](https://github.com/miguelgrinberg/flask-socketio/issues/22): document use of nginx as a reverse proxy ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9ed9b070cccd98be88ce3b3de0f684e4601924db))
- [#28](https://github.com/miguelgrinberg/flask-socketio/issues/28): example app did not start background thread when running under a production server ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/6c995a56b400f165fde9be63b29310fde17974fc))

**Release 0.3.7** - 2014-05-21

- [#31](https://github.com/miguelgrinberg/flask-socketio/issues/31): show host and port on startup ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/43bc6782ec73cce90262ede5bec579f8d0b967c0))

**Release 0.3.6** - 2014-05-13

- [#26](https://github.com/miguelgrinberg/flask-socketio/issues/26): threading error during exit ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/aa6f65fafd55568d12de75362e8726cde52a7ba2))
- added gevent dependency ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/52bcba3e39e00475e002e28c7733e43071d7f344))

**Release 0.3.5** - 2014-05-07

- [#23](https://github.com/miguelgrinberg/flask-socketio/issues/23): incorrect use of run_with_reloader ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a0c3072f5948d1dac60653c0d8fce5c37a33843f))

**Release 0.3.4** - 2014-04-27

- show a more friendly error when a server that is not compatible with gevent-socketio is used ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a58879f3d4db7e4e1e9b9a0cede2371b3cb1979f))
- added short deployment section to docs ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/93008853131e86a80737fb1a3defa38a763f0f35))
- correct syntax for js imports ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/f3491f6ea9d327ada68de7b0f7fe1c76f2767642))
- [#18](https://github.com/miguelgrinberg/flask-socketio/issues/18): server initiated communication does not work on the global namespace ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/21695aba5930e17b09cfb23bea1a273737b647fb))

**Release 0.3.3** - 2014-04-22

- [#19](https://github.com/miguelgrinberg/flask-socketio/issues/19): use Flask's JSON serializers in gevent-socketio ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/44c1453170345c7a032bede3b1ccc0ffba18b92d))
- Correct URL to socket.io.min.js Fails in IE otherwise ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/7e1542852a7e9c307ef0600d51bcf09e2ce642ba)) (thanks **Richard Morrison**!)

**Release 0.3.2** - 2014-03-31

- [#14](https://github.com/miguelgrinberg/flask-socketio/issues/14): access to server object when using gunicorn ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/1fb766c89f09dd814f4a62c693bf0c3b8318aecc))

**Release 0.3.1** - 2014-03-24

- Cleanup of kwargs passthrough ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/8c8232853e9451a6f51825b2c3240605941038e8)) (thanks **ijustdrankwhat**!)
- pop[] => pop('resource', None) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9b82e0716141be53badc8f208a647470c975055a)) (thanks **ijustdrankwhat**!)
- Allow SocketIOServer keywords to get passed through Allow keyword passthrough at run() ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/378d75c5166a12920d1dd225ba8f75c88fc6d542)) (thanks **Shep.Walker**!)
- added server pushed events to example app ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/3c06500d933d16120c9f38027abe6959fe83f08c))
- monkey patch early ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/4f9d0fade14272f4f896e2fdd0f513393b4c5361))
- travis ci builds ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/c5f60e012926a76a1cc9f7507f07f1f088b9d362))
- travis ci builds ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/b0d14b0b20dde79a705ff5ebafb4f40dfe368826))

**Release 0.3** - 2014-03-08

- Support for rooms ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/764932e5cae52883b7d2d8884e380e8b25f3d68f))
- update example requirements ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/a817068511d0ed8fd50141d31b83a7256ef56094))
- more tests, 83% coverage ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/386c9a9b1881a6a239165f0f8394202f9c1fa4f3))
- more tests ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/fa7816298ce5fb87a41f91227443e5eba5d910db))

**Release 0.2.2** - 2014-02-19

- forgot self ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/8e76e6de7983ec9c990e2aea6d263a569915156a)) (thanks **Mark McGuire**!)
- Return handler response (for client requested ack) ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/78682ef75788b97badf8f4c4c0c89db65c89fed3)) (thanks **Mark McGuire**!)
- Use counter for sessid ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/fb11792f87ebf78576f6be859a9a019dfadeb211)) (thanks **Mark McGuire**!)
- Add returns for methods ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/7663d9f108edf2580f81342eaaf9fc9a66312ea9)) (thanks **Mark McGuire**!)
- Actually import random ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/239c2b713c791b41509ee95171b2c648b026f499)) (thanks **Mark McGuire**!)
- Add sessid to socket ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/898447f7d07afa751bb7e7b8374a18c6751df140)) (thanks **Mark McGuire**!)
- unit testing framework ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9633aba98d4b54325d1e33f0e3329e168b3b2445))
- [#2](https://github.com/miguelgrinberg/flask-socketio/issues/2): removed old code not intended for release ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/b21e23ab3595cb4203aee6325f43a80e1adccb3b))
- [#6](https://github.com/miguelgrinberg/flask-socketio/issues/6): save session variables correctly ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/173876eb31f03e6b99419e9b6cc7f3a2b1463074))

**Release 0.2** - 2014-02-13

- Updated documentation ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/2c3d883c3027c2c3663d32b60129e10886fba60e)) (thanks **Axel Haustant**!)
- Run the sample app in debug mode ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/b71bfa7ad02d20dad1a3557455135f5b7403c931)) (thanks **Axel Haustant**!)
- Added werkzeug debugger support ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/9b1716aa35c81d374d902d49f36d7ed341cb8bd1)) (thanks **Axel Haustant**!)
- first release ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/be1d74829f3a8f2c29898181bdf81d78748c8e3b))
- Initial commit ([commit](https://github.com/miguelgrinberg/flask-socketio/commit/63db33d193e651b5df8a0ae305098dbb33832a58))
