# System
import os

# Packages
from django.views.generic.base import TemplateView
from django.http import Http404
from django.conf import settings
import frontmatter
import mistune


def _absolute_template_path(path, origin_filepath):
    """
    Infer an absolute path to a template from a partial path

    - If the path starts with a "/",
      simply prepend it with settings.TEMPLATE_FINDER_PATH
    - If the path doesn't start with a "/",
      work out the absolute path relative to the origin_filepath
    """

    if path.startswith("/"):
        # "absolute" path, simply use the TEMPLATE_FINDER_PATH root
        template_filepath = os.path.join(
            settings.TEMPLATE_FINDER_PATH, path.lstrip("/")
        )
    else:
        # "relative" path, use the existing filepath
        directory = os.path.dirname(origin_filepath)
        template_filepath = os.path.abspath(os.path.join(directory, path))

    return template_filepath


def _find_matching_template(path):
    """
    Given a basic path, find an HTML or Markdown file
    """

    # Build basic search path
    base_filepath = os.path.join(
        settings.TEMPLATE_FINDER_PATH, path.strip("/")
    )

    # Try to match HTML or Markdown files
    if os.path.isfile(base_filepath + ".html"):
        matched_filepath = base_filepath + ".html"
    elif os.path.isfile(base_filepath + "/index.html"):
        matched_filepath = base_filepath + "/index.html"
    elif os.path.isfile(base_filepath + ".md"):
        matched_filepath = base_filepath + ".md"
    elif os.path.isfile(base_filepath + "/index.md"):
        matched_filepath = base_filepath + "/index.md"

    return matched_filepath


class TemplateFinder(TemplateView):
    parse_markdown = mistune.Markdown(
        parse_block_html=True,
        parse_inline_html=True,
    )

    def _parse_markdown_file(self, filepath):
        """
        Parse a markdown file into the relevant parts.

        - html_content: The parsed HTML from the Markdown content
        - context: Any "includes" and custom "context" specified in frontmatter
        - template_filepath: An absolute filepath inferred from the frontmatter
        """

        # Parse frontmatter, and add it to context
        markdown = frontmatter.load(filepath)

        # Set the template path
        wrapper_template = markdown.metadata.get("wrapper_template")
        context = markdown.metadata.get("context", {})

        if not wrapper_template:
            # If no wrapper template specified,
            # this doesn't count as a valid Markdown file
            return None

        if wrapper_template:
            template_filepath = _absolute_template_path(
                wrapper_template, filepath
            )
        else:
            template_filepath = None

        # Parse core HTML content
        context["html_content"] = self.parse_markdown(markdown.content)

        # Add any Markdown includes
        for key, path in markdown.metadata.get(
            "markdown_includes", {}
        ).items():
            include_path = _absolute_template_path(path, filepath)

            with open(include_path) as include:
                context[key] = self.parse_markdown(include.read())

        return {"context": context, "template_filepath": template_filepath}

    def render_to_response(self, context, **response_kwargs):
        """
        Return a response, using the `response_class` for this view, with a
        template rendered with the given context.
        Pass response_kwargs to the constructor of the response class.
        """

        template_filepath = None

        # Response defaults
        response_kwargs.setdefault("content_type", self.content_type)

        # Find .html or .md template files
        template_filepath = _find_matching_template(self.request.path)

        # If we found a Markdown file, parse it to find its wrapper template
        if template_filepath.endswith(".md"):
            markdown_data = self._parse_markdown_file(template_filepath)
            template_filepath = markdown_data["template_filepath"]
            context.update(markdown_data["context"])

        # If we couldn't find the template, show 404
        if not template_filepath:
            raise Http404("Can't find template for " + self.request.path)

        # Send the response
        return self.response_class(
            request=self.request,
            template=template_filepath,
            context=context,
            using=self.template_engine,
            **response_kwargs
        )

    def get_template_names(self):
        """
        Template finding and parsing is now handled in
        render_to_response(), and so get_template_names is
        not needed
        """

        raise NotImplementedError()
