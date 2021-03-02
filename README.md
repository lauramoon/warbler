### Warbler
Warbler is a bare-bones Twitter clone running on Flask with postgreSQL.

To run locally, create a database named 'wabler'. The seed file provides many sample users and messages.

This site allows users to post messages, like other users' messages, and follow and unfollow other users. It does not implement private messages, private accounts, user blocking, or admin accounts.

The tests require a database named 'warbler-test'. The views tests were somewhat tedious to write, but were helpful when adding macros.

The like and follow buttons are not efficient, currently reloading the page with every click. But I wanted to explore the use of macros and hidden fields to track redirects, so I haven't implemented more efficient front-end options.