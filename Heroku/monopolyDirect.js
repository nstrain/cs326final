/**
 * This module implements direct, Android-to-Postgres access to the Monopoly DB.
 * The database is hosted on ElephantSQL.
 *
 * Because the username and password are stored as Heroku config vars, store
 * those values in .env and the run this module using the Procfile script:
 *
 *      heroku local direct
 *
 * @author: kvlinden
 * @date: Summer, 2020
 */

// Set up the database connection.
const pgp = require('pg-promise')();
const db = pgp({
    host: "queenie.db.elephantsql.com",
    port: 5432,
    database: process.env.USER,
    user: process.env.USER,
    password: process.env.PASSWORD
});

// Send the SQL command directly to Postgres.
db.many("SELECT * FROM Devices")
    .then(function (data) {
        console.log(data);
    })
    .catch(function (error) {
        console.log('ERROR:', error)
    });
