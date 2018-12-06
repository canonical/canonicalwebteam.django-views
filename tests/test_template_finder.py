# Core
import os
import unittest

# Packages
import django
from django.conf import settings
from django.test import Client


this_dir = os.path.dirname(os.path.realpath(__file__))

# Mock Django
settings.configure(
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [f"{this_dir}/fixtures/templates"],
        }
    ],
    ROOT_URLCONF="tests.fixtures.urls",
)
django.setup()


class TestTemplateFinder(unittest.TestCase):
    django_client = Client()

    def test_404(self):
        """
        When given a URL to a non-existent file,
        return a 404
        """

        response_one = self.django_client.get("/missing-file")
        response_two = self.django_client.get("/missing-file.html")

        self.assertEqual(response_one.status_code, 404)
        self.assertEqual(response_two.status_code, 404)

    def test_direct_files(self):
        """
        When given a URL to an html file (without the HTML extension),
        check we get the file content
        """

        response_one = self.django_client.get("/a-file")
        response_two = self.django_client.get("/a-directory/another-file")

        self.assertEqual(response_one.status_code, 200)
        self.assertEqual(response_one.content, b"top level file\n")

        self.assertEqual(response_two.status_code, 200)
        self.assertEqual(response_two.content, b"second level file\n")

    def test_index_files(self):
        """
        When given a URL to a directory with an index.html
        check we get the index.html content
        """

        response_one = self.django_client.get("/")
        response_two = self.django_client.get("/a-directory")

        self.assertEqual(response_one.status_code, 200)
        self.assertEqual(response_one.content, b"homepage\n")

        self.assertEqual(response_two.status_code, 200)
        self.assertEqual(response_two.content, b"subpath index\n")

    def test_case_insensitive_url(self):
        """
        If a mixed-case URL is provided, which would match a filepath
        case-insensitively, a redirect should be returned to the correct
        URL for the file
        """

        response_one = self.django_client.get("/A-dIreCtory")
        response_two = self.django_client.get("/a-FILe")
        response_three = self.django_client.get("/a-directory/anoTHer-File")
        response_four = self.django_client.get("/a-DIRectoRY/ANOther-FILE")
        response_five = self.django_client.get("/a-directory/mixed-case")

        self.assertEqual(response_one.status_code, 302)
        self.assertEqual(response_one.get("location"), "/a-directory")
        self.assertEqual(response_two.status_code, 302)
        self.assertEqual(response_two.get("location"), "/a-file")
        self.assertEqual(response_three.status_code, 302)
        self.assertEqual(
            response_three.get("location"), "/a-directory/another-file"
        )
        self.assertEqual(response_four.status_code, 302)
        self.assertEqual(
            response_four.get("location"), "/a-directory/another-file"
        )
        self.assertEqual(response_five.status_code, 302)
        self.assertEqual(
            response_five.get("location"), "/a-directory/mIXed-CAse"
        )

    def test_markdown_files_without_wrapper_template(self):
        """
        If a Markdown file doesn't have `wrapper_template` in the frontmatter,
        it should be disregarded, and result in a 404
        """

        response_one = self.django_client.get("/md-files")
        response_two = self.django_client.get("/md-files/a-file")

        self.assertEqual(response_one.status_code, 404)
        self.assertEqual(response_two.status_code, 404)

    def test_markdown_direct_files(self):
        """
        Check a correctly configured markdown file is correctly parsed
        and returned, when requested with its URL path
        """

        response = self.django_client.get("/md-templates/a-file")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"a <em>md</em> file" in response.content)

    def test_markdown_index_files(self):
        """
        Check a correctly configured index.md file is correctly parsed
        and returned, when requested with its URL path
        """

        response = self.django_client.get("/md-templates")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"<strong>index</strong> file" in response.content)

    def test_markdown_includes(self):
        """
        Check the `markdown_includes` frontmatter property will find and parse
        an included Markdown file correctly, and pass it through to the
        `markdown_wrapper` template.
        """

        response_one = self.django_client.get("/md-templates")
        response_two = self.django_client.get("/md-templates/a-file")
        self.assertTrue(
            b'<a href="https://example.com">a link</a>' in response_one.content
        )
        self.assertTrue(
            b'<a href="https://example.com">a link</a>' in response_two.content
        )

    def test_markdown_context(self):
        """
        Check `context` frontmatter can successfully be passed through to the
        `markdown_wrapper` template.
        """

        response = self.django_client.get("/md-templates")
        self.assertTrue(b"The index page" in response.content)


if __name__ == "__main__":
    unittest.main()
