#!/usr/bin/env python
#
# Copyright (c) 2021-2024 Jeroen Overschie <jeroen@darius.nl>
# Copyright (c) 2024 Akarsh Simha <akarsh@kde.org>
#
# Adapted from eml-to-html package by Jeroen Overschie
# https://pypi.org/project/eml-to-html/
#
# SPDX-License-Identifier: MIT

from email import message_from_file
from email.message import Message
from pathlib import Path
import sys
from typing import Any, List, Union, Dict
import hashlib
import os
import re
from markdownify import MarkdownConverter

class CustomMarkdownConverter(MarkdownConverter):
    def convert_div(self, el, text, convert_as_inline):
        return super().convert_p(el, text, convert_as_inline)

def markdownify(html: str, **options) -> str:
    return CustomMarkdownConverter(**options).convert(html)

INTERACTIVE = os.getenv('INTERACTIVE')
if INTERACTIVE is not None:
    from IPython import embed
else:
    def embed(**kwargs):
        return

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = SCRIPT_DIR / ".." / "docs"

def unique_filename(_input: bytes) -> str:
    # Courtesy of Google Gemini
    # random_bytes = secrets.token_bytes(20)  # 20 bytes for SHA1
    hash_object = hashlib.sha1()
    hash_object.update(_input)
    return hash_object.hexdigest()

class MessageContent:
    data: bytes = None
    mimetype: str = None

class HTMLContent(MessageContent):
    charset: str = None

class ImageContent(MessageContent):
    filename: str = None # Filename
    orig_filename: str = None # Original Filename
    cid: str = None # Content-ID
    subtype: str = None# jpeg / png etc.

def extract_message_contents(message: Message) -> List[MessageContent]:
    result = []
    mimetype = message.get_content_type()
    if mimetype == 'multipart/related':
        payload: List = message.get_payload()
        assert isinstance(payload, List), type(payload)
        for content in payload:
            result.extend(extract_message_contents(content))
    elif mimetype == 'multipart/alternative':
        payload: List = message.get_payload()
        assert isinstance(payload, List), type(payload)
        alternatives = {x.get_content_type(): x for x in payload}
        for ty in ['text/html', 'text/plain']:
            if ty in alternatives:
                result.extend(extract_message_contents(alternatives[ty]))
                break
        else:
            raise ValueError(f'Unhandled mimetype {ty} within multipart/alternative')
    elif mimetype.startswith('text/'): # Both text/html and text/plain are treated the same since we'll embed into a markdown
        content = HTMLContent()
        content.mimetype = mimetype
        content.data = message.get_payload(decode=True)
        assert len(message.get_charsets()) == 1, message.get_charsets()
        content.charset = message.get_charsets()[0]
        result.append(content)
    elif mimetype.startswith('image/'):
        content = ImageContent()
        content.mimetype = mimetype
        content.data = message.get_payload(decode=True)
        content.orig_filename = message.get_filename()
        content.cid = message['Content-ID'].lstrip('<').rstrip('>')
        content.subtype = message.get_content_subtype()
        result.append(content)
    else:
        embed(header=f'Handle {mimetype}')
        print(f"🟡 Ignoring attachment of unhandled mimetype {mimetype}")
    return result


def eml_to_md(eml_path_str: Union[str, Path]) -> Path:
    eml_path: Path = Path(eml_path_str)
    if not eml_path.is_file():
        print(f"🟡 Skipping `{eml_path}`; is not a file")

    if eml_path.suffix != ".eml":
        print(f"🟡 Skipping `{eml_path}`; not an .eml file")

    bad_filename_chars = re.compile('[ \'\(\):]')
    md_path: Path = DOCS_DIR / bad_filename_chars.sub('_', eml_path.with_suffix('.md').name)
    with eml_path.open(mode="r") as eml_file:
        message: Message = message_from_file(eml_file)
        contents: List[MessageContent] = extract_message_contents(message)

        # Write preamble
        preamble_table = {
            'layout': 'default',
            'title': '"' + message['Subject'] + '"', # Quoted version of subject
            'author': re.sub(' *<[^>]*> *$', '', message['From']), # Strip email from "From" field
            'date': '"' + message['Date'] + '"', # Date of email
        }
        # Process content
        main_content = [content for content in contents if isinstance(content, HTMLContent)]
        attachments = [content for content in contents if not isinstance(content, HTMLContent)]
        if len(main_content) != 1:
            embed(header=f'Multiple or non-existing main content. Investigate.')
            raise NotImplementedError(f'Unhandled situation with {len(main_content)} main content parts')
        main_content = main_content[0]
        if main_content.mimetype == 'text/html':
            non_inline_attachments = []
            for attachment in attachments:
                # Replace inline attachments
                if not attachment.mimetype.startswith('image/'):
                    raise NotImplementedError(f'Unhandled attachment mimetype {attachment.mimetype}')
                filename = f'assets/{unique_filename(attachment.data)}.{attachment.mimetype.split("/")[1]}'
                cid_pattern = re.compile(('"cid:' + re.escape(attachment.cid) + '"').encode(main_content.charset), re.IGNORECASE) # FIXME: Do we also have to do a filename search?
                attachment.filename = filename # Write in our unique filename
                if cid_pattern.search(main_content.data) is None:
                    non_inline_attachments.append(attachment)
                else:
                    main_content.data = cid_pattern.sub(filename.encode(main_content.charset), main_content.data)
            main_content.data = markdownify(main_content.data.decode(main_content.charset), heading_style='ATX', ).encode(main_content.charset)
        else:
            print(f"🟡 No special post-processing performed for main content of type {main_content.mimetype}")
            non_inline_attachments = attachments

        # Attach non-inline attachments
        for attachment in non_inline_attachments:
            main_content.data += ('\n\n' + f'![{attachment.orig_filename}]({attachment.filename})')

        # Write main content
        if main_content.charset != 'utf-8':
            print(f"🟡 Warning: Content encoding is not utf-8")
        with md_path.open(mode="wb") as md_file:
            # Preamble table
            md_file.write(('\n'.join(['---',] +
                                    [f'{key}: {value}' for key, value in preamble_table.items()] + ['---', ''])).encode(main_content.charset))

            md_file.write(main_content.data)

        # Write attachments
        attachment_paths = []
        for attachment in attachments:
            attachment_path = DOCS_DIR / Path(attachment.filename)
            if attachment_path.exists():
                print(f"🟡 Already existing attachment at {attachment_path} will be overwritten!")
            with attachment_path.open(mode="wb") as attachment_file:
                attachment_file.write(attachment.data)
            attachment_paths.append(attachment_path)

    print(f"🟢 Job complete, output at {md_path}. Attachments at\n\t" + '\n\t'.join(map(str, attachment_paths)))

    return md_path


def main():
    file_paths: List[str] = sys.argv[1:]

    for file_path in file_paths:
        eml_to_md(file_path)


if __name__ == "__main__":
    main()
