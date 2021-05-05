/**
 * This module implements a REST-inspired webservice for the Monopoly DB.
 * The database is hosted on ElephantSQL.
 *
 * Currently, the service supports the player table only.
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

// Configure the server and its routes.

const express = require('express');
const app = express();
const port = process.env.PORT || 3000;
const router = express.Router();
router.use(express.json());


router.get("/devices", readDevices);
router.put("/devices/:name/:status", updateDevice);

//app.use(router);
//app.use(errorHandler);
app.use(function(req, res, next) {
    res.header("Access-Control-Allow-Origin", '*');
    res.header("Access-Control-Allow-Credentials", true);
    res.header('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS');
    res.header("Access-Control-Allow-Headers", 'Origin,X-Requested-With,Content-Type,Accept,content-type,application/json');
    next();
}, router, errorHandler);
//app.use(cors());
app.listen(port, () => console.log(`Listening on port ${port}`));

// Implement the CRUD operations.

function errorHandler(err, req, res) {
    if (app.get('env') === "development") {
        console.log(err);
    }
    res.sendStatus(err.status || 500);
}

function returnDataOr404(res, data) {
    if (data == null) {
        res.sendStatus(404);
    } else {
        res.send(data);
    }
}


function readDevices(req, res, next) {
    db.many("SELECT name, status FROM Devices")
        .then(data => {
            res.send(data);
        })
        .catch(err => {
            next(err);
        })
}


function updateDevice(req, res, next) {
    console.log(`UPDATE Devices SET status=${req.params.status} WHERE name='${req.params.name}' RETURNING mac`);
    db.oneOrNone(`UPDATE Devices SET status=${req.params.status} WHERE name='${req.params.name}' RETURNING mac`, req.body)
        .then(data => {
            returnDataOr404(res, data);
        })
        .catch(err => {
            next(err);
        });
}
