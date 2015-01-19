# How to contribute

Third-party patches are essential for keeping puppet great. We simply can't
access the huge number of platforms and myriad configurations for running
puppet. We want to keep it as easy as possible to contribute changes that
get things working in your environment. There are a few guidelines that we
need contributors to follow so that we can have a chance of keeping on
top of things.

## Getting Started

* Make sure you have a [Jira account](TBD)
* Make sure you have a [GitHub account](https://github.com/signup/free)
* Serach for existing ticktes matching your issue and if none are found submit one.
  * Provide a clear description of the issue including any configuration information.
  * Provide clear reproduction steps. 
* Fork the repository on GitHub

## Making Changes

* Create a topic branch from where you want to base your work.
  * This is usually the master branch.
  * Only target release branches if you are certain your fix must be on that
    branch.
  * To quickly create a topic branch based on master; `git checkout -b
    fix/master/my_contribution master`. Please avoid working directly on the
    `master` branch.
* Make commits of logical units.
* Check for unnecessary whitespace with `git diff --check` before committing.
* Make sure your commit messages are in the proper format.

````
    (BS-1234) Super awesome feature incoming.

    With the addition of this patch cats can now fly, pigs can speak, and
    dogs are vegans. 
````

* Make sure you have added the necessary tests for your changes.
  * Untested code will not be merged!
* Run _all_ the tests to assure nothing else was accidentally broken.
  * AGAIN... untested code will not be merged!

## Making Trivial Changes

### Documentation

For changes of a trivial nature to comments and documentation, it is not
always necessary to create a new ticket in Jira. In this case, it is
appropriate to start the first line of a commit with '(doc)' instead of
a ticket number. 

````
    (doc) Add documentation commit example to CONTRIBUTING

    There is no example for contributing a documentation commit
    to the Bespoke repository. This is a problem because the contributor
    is left to assume how a commit of this nature may appear.

    The first line is a real life imperative statement with '(doc)' in
    place of what would have been the ticket number in a 
    non-documentation related commit. The body describes the nature of
    the new documentation or comments added.
````

## Submitting Changes

* Push your changes to a topic branch in your fork of the repository.
* Submit a pull request to the repository in the "Fancy Lads" organization.
* Update your Jira ticket to mark that you have submitted code and are ready for it to be reviewed (Status: Ready for Merge).
  * Include a link to the pull request in the ticket.
* After feedback has been given we expect responses within two weeks. After two
  weeks we may close the pull request if there is no activity.

# Additional Resources

* TBD