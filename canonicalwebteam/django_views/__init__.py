# System
import os

# Packages
import frontmatter
import glob
import re
from django.http import Http404, HttpResponseRedirect
from django.template import Context, loader, TemplateDoesNotExist
from django.views.generic.base import TemplateView
from mistune import Markdown, BlockLexer


def _insensitive_glob(pattern, base_dir):
    """
    Look for files with glob patterns,
    but case ignoring case
    """

    def either(c):
        return "[%s%s]" % (c.lower(), c.upper()) if c.isalpha() else c

    search = "".join(map(either, pattern))
    search_path = os.path.join(base_dir, search)

    return glob.glob(search_path)


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


def _find_template_url(path):
    """
    Look for a template by:
    - checking for case-insensitive matches
    - seeing if the URL exactly matches the filename,
      with extension
    """

    matches = []

    template_dirs = loader.engines.templates["django"]["DIRS"]

    for template_dir in template_dirs:
        for match in (
            _insensitive_glob(path, template_dir)
            + _insensitive_glob(path + ".html", template_dir)
            + _insensitive_glob(path + ".md", template_dir)
        ):
            cleaned_match = re.sub(r"^" + template_dir, "", match)
            cleaned_match = re.sub(r"\.(html|md)$", "", cleaned_match)
            matches.append(cleaned_match)

    # Only return a found template if we found only one
    if (
        len(matches) == 1
        and matches[0].lower() == "/" + path.lower()
        and _get_template(matches[0].lstrip("/"))
    ):
        return matches[0]


def _relative_template_path(path, origin_filepath):
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


def _get_template(url_path):
    """
    Given a basic path, find an HTML or Markdown file
    """

    # Try to match HTML or Markdown files
    if _template_exists(url_path + ".html"):
        return url_path + ".html"
    elif _template_exists(os.path.join(url_path, "index.html")):
        return os.path.join(url_path, "index.html")
    elif _template_exists(url_path + ".md"):
        return url_path + ".md"
    elif _template_exists(os.path.join(url_path, "index.md")):
        return os.path.join(url_path, "index.md")

    return None


class WebteamBlockLexer(BlockLexer):
    list_rules = (
        "newline",
        "block_code",
        "fences",
        "lheading",
        "hrule",
        "table",
        "nptable",
        "block_quote",
        "list_block",
        "block_html",
        "text",
    )


class TemplateFinder(TemplateView):
    parse_markdown = Markdown(
        parse_block_html=True,
        parse_inline_html=True,
        block=WebteamBlockLexer(),
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

        template_filepath = _relative_template_path(wrapper_template, filepath)

        # Parse core HTML content
        context["html_content"] = self.parse_markdown(markdown.content)

        # Add any Markdown includes
        for key, path in markdown.metadata.get(
            "markdown_includes", {}
        ).items():
            include_path = _relative_template_path(path, filepath)
            include_content = loader.get_template(
                include_path
            ).template.render(Context())
            context[key] = self.parse_markdown(include_content)

        return {"context": context, "template": template_filepath}

    def render_to_response(self, context, **response_kwargs):
        """
        Return a response, using the `response_class` for this view, with a
        template rendered with the given context.
        Pass response_kwargs to the constructor of the response class.
        """

        # Response defaults
        response_kwargs.setdefault("content_type", self.content_type)

        # Find .html or .md template files
        path = self.request.path.lstrip("/")
        matching_template = _get_template(path)

        # If we couldn't find the template, show 404
        if not matching_template:
            found_template_url = _find_template_url(path)

            if found_template_url:
                return HttpResponseRedirect(found_template_url)
            else:
                raise Http404("Can't find template for " + self.request.path)

        # If we found a Markdown file, parse it to find its wrapper template
        if matching_template.endswith(".md"):
            markdown_data = self._parse_markdown_file(matching_template)

            if not markdown_data:
                raise Http404(
                    self.request.path + " not correctly configurated."
                )

            matching_template = markdown_data["template"]
            context.update(markdown_data["context"])

        # Send the response
        return self.response_class(
            request=self.request,
            template=matching_template,
            context=context,
            using=self.template_engine,
            **response_kwargs
        )
