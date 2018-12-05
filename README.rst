canonicalwebteam.django\_views
==============================

|CircleCI build status| |Code coverage|

Views for Django apps, primarily for use in Webteam Django apps.

Installation
------------

You can install this module directly with
``pip install canonicalwebteam.django_views``, or alternatively, include
``canonicalwebteam.django_views`` in ``requirements.txt`` for your app.

TemplateFinder
--------------

``TemplateFinder`` is an extension of ``TemplateView`` which attempts to
load the corresponding templates directly from URLs, without the need to
write a view for each URL.

It can load HTML templates directly, or parse Markdown files that
contain a "wrapper\_template" frontmatter key.

Usage
~~~~~

Here's an example of how to make use of ``TemplateFinder`` in your
Django app:

.. code:: python
    # urls.py
    from django.conf.urls import url
    from canonicalwebteam.django_views import TemplateFinder
    # ...
    urlpatterns += url(r"$^", TemplateFinder.as_view()),

Template matching
~~~~~~~~~~~~~~~~~

When the app parses a URL, it will look for templates in the following
locations, in order:

-  ``/parent/location/`` =>
   ``templates/parent/location.html``
-  ``/parent/location/`` =>
   ``templates/parent/location/index.html``
-  ``/parent/location/`` =>
   ``templates/parent/location.md``
-  ``/parent/location/`` =>
   ``templates/parent/location/index.md``

Markdown parsing
~~~~~~~~~~~~~~~~

If the ``TemplateFinder`` encounters a Markdown file (ending ``.md``) it
will look for the following keys in `YAML
frontmatter <https://jekyllrb.com/docs/front-matter/>`__:

-  ``wrapper_template`` *mandatory*: (e.g.:
   ``wrapper_template: /includes/markdown-wrapper.html``) A path to an
   HTML template within which to place the parsed markdown content. If
   the path doesn't have a leading slash (e.g. "templates/template.html"
   or "../templates/template.html"), then ``TemplateFinder`` will search
   for the template relative to the location of the Markdown file in
   question. If the path
-  ``context`` *optional*: (e.g.:
   ``context: {title: "Welcome", description: "A welcome page"}``) A
   dictionary of extra key / value pairs to pass through to the template
   context.
-  ``markdown_includes`` *optional*: (e.g.:
   ``markdown_includes: {nav: }``) A mapping of key names to template
   paths pointing to Markdown files to include. Each template path will
   be parsed, the resulting HTML will be passed in the template context,
   under the relevant key.

Here's an example Markdown file:

.. code:: markdown

    ---
    wrapper_template: "/includes/markdown-wrapper.html"
    markdown_includes:
      nav: "includes/nav.md"
    context:
      title: "Welcome"
      description: "A welcome page"
    ---

    Welcome to my website.

    ## GitHub

    I also have [a GitHub page](https://github.com/me).

.. |CircleCI build status| image:: https://circleci.com/gh/canonical-webteam/yaml-responses.svg?style=shield
   :target: https://circleci.com/gh/canonical-webteam/yaml-responses
.. |Code coverage| image:: https://codecov.io/gh/canonical-webteam/yaml-responses/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/canonical-webteam/yaml-responses

