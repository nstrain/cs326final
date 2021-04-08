# CS 262 Monopoly Webservice

This is the data service application for the [CS 262 sample Monopoly project](https://github.com/calvin-cs262-organization/monopoly-project) 
and it is deployed here:
          
<https://vast-spire-73678.herokuapp.com/players/>

It is based on the standard Heroku with Node.js tutorial.

<https://devcenter.heroku.com/articles/getting-started-with-nodejs>  

The database is relational with the schema specified in the `sql/` sub-directory,
 and is hosted on [ElephantSQL](https://www.elephantsql.com/). The database user
and password are stored as Heroku configuration variables rather than in this (public) repo.

We implement this sample as a separate repo to simplify Heroku integration, but 
for lab 9, you can simply submit your code under the standard `cs262/lab09` directory. 
For the team project, configure your Heroku app to auto-deploy the code from the
master/main branch of your
service repo; do this by following the instructions under the &ldquo;Deploy&rdquo; 
tab in your application in the Heroku dashboard.
 