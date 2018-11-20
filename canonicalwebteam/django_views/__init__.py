# System
import os

# Packages
from django.http import Http404
from django.template import Context, loader, TemplateDoesNotExist
from django.views.generic.base import TemplateView
import frontmatter
from mistune import Markdown, BlockLexer, BlockGrammar


def _template_exists(path):
    """
    Check if a template exists
    without raising an exception
    """

    try:
        loader.get_template(path)
        return True
    except TemplateDoesNotExist:
        return False


def _template_path(path, origin_filepath):
    """
    Infer a path to a template from a partial path

    - If the path starts with a "/",
      simply ask Django to locate the template
    - If the path doesn't start with a "/",
      work out the absolute path relative to the origin_filepath
    """

    if path.startswith("/"):
        # "absolute" path, just strip the leading "/"
        # so template loader can do its work
        path = path.lstrip("/")
    else:
        # "relative" path, use the existing filepath
        path = os.path.relpath(
            os.path.join(os.path.dirname(origin_filepath), path)
        )

    return path


def _find_matching_template(path):
    """
    Given a basic path, find an HTML or Markdown file
    """

    # Try to match HTML or Markdown files
    if _template_exists(path + ".html"):
        return path + ".html"
    elif _template_exists(os.path.join(path, "index.html")):
        return os.path.join(path, "index.html")
    elif _template_exists(path + ".md"):
        return path + ".md"
    elif _template_exists(os.path.join(path, "index.md")):
        return os.path.join(path, "index.md")

    return None


class WebteamBlockLexer(BlockLexer):
    list_rules = (
        'newline', 'block_code', 'fences', 'lheading', 'hrule',
        'table', 'nptable',
        'block_quote', 'list_block', 'block_html', 'text',
    )


class TemplateFinder(TemplateView):
    parse_markdown = Markdown(
        parse_block_html=True, parse_inline_html=True,
        block=WebteamBlockLexer()
    )

    def _parse_markdown_file(self, filepath):
        """
        Parse a markdown file into the relevant parts.

        - html_content: The parsed HTML from the Markdown content
        - context: Any "includes" and custom "context" specified in frontmatter
        - template_filepath: An absolute filepath inferred from the frontmatter
        """

        # Parse frontmatter, and add it to context
        markdown_template = loader.get_template(filepath)
        file_contents = markdown_template.template.render(Context())
        markdown = frontmatter.loads(file_contents)

        # Set the template path
        wrapper_template = markdown.metadata.get("wrapper_template")
        context = markdown.metadata.get("context", {})

        if not wrapper_template:
            # If no wrapper template specified,
            # this doesn't count as a valid Markdown file
            return None

        if wrapper_template:
            template_filepath = _template_path(
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
            include_path = _template_path(path, filepath)
            include_content = loader.get_template(
                include_path
            ).template.render(Context())
            context[key] = self.parse_markdown(include_content)

        return {
            "context": context,
            "template_filepath": template_filepath,
        }

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
        template_filepath = _find_matching_template(
            self.request.path.lstrip("/")
        )

        # If we couldn't find the template, show 404
        if not template_filepath:
            raise Http404("Can't find template for " + self.request.path)

        # If we found a Markdown file, parse it to find its wrapper template
        if template_filepath.endswith(".md"):
            markdown_data = self._parse_markdown_file(template_filepath)
            template_filepath = markdown_data["template_filepath"]
            context.update(markdown_data["context"])

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
