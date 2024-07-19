---
layout: default
title: Example MarkDown Page
author: Akarsh Simha
---

This is an example of how the simple "markup" language called MarkDown
can be used to create websites for Adventures in Deep Space. There are
many MarkDown tutorials on the internet, but we want to provide a
quick intro here.

## Preamble

Every markdown page starts with a "Front Matter" or preamble, which contains the following format:

```
---
layout: default
title: <Title of the Page>
author: <Your Name>
---
```

The title should not contain the "Adventures in Deep Space", doing
that in the page title is taken care of by our HTML generation engine

## Sub-headings

You can create different levels of headings by using different number
of # marks before the heading content. I suggest starting with level-two
headings (i.e. two # marks before the heading) since the title of the
page uses the first-level heading.

## Bold, italics etc.

Bold text is marked with \*\* around it, e.g. \*\*bold text\*\*
produces **bold text**.

Italics are marked with either a single \* or a single \_,
e.g. \_emphasize\_ produces _emphasize_.

## Blockquotes

Blockquotes are prefixed with \>. So for example adding the line:

\> Use high power to observe the \_tiny\_ knots in the galaxy

produces:

> Use high power to observe the _tiny_ knots in the galaxy



## Annotating DSOs

We have some SIMBAD integration in place for handling DSO
names. Usually this is used the first time you introduce the DSO, so
that a SIMBAD page can be displayed upon hovering the mouse cursor on
the DSO name.

To attach this feature to a DSO name, simply mark it with `<x-dso>`
HTML tags as follows:

```
<x-dso>NGC 1999</x-dso>
```

This produces:
<x-dso>NGC 1999</x-dso>

If the name is not understood by SIMBAD, you can do the following:
```
> Consider observing <x-dso simbad="PN A66 37">Abell 37</x-dso> and <x-dso simbad="K79 54">KTG 54</x-dso>.
```
to get:

> Consider observing <x-dso simbad="PN A66 37">Abell 37</x-dso> and <x-dso simbad="K79 54">KTG 54</x-dso>.

## Links

A link can be added by putting square brackets around the text and putting the URL in parantheses:
```
Also check out the [Deep Sky Forum](https://deepskyforum.com)
```
produces the following:

Also check out the [Deep Sky Forum](https://deepskyforum.com)

## Images

The method to add an image is very similar to a link, except there is an `!` before:
```
![Abell 70](assets/abell70.jpg)
```

produces

![Abell 70](assets/abell70.jpg)

The text `Abell 70` went into the alternative text for the image which
will be used in case the image cannot be rendered and helps
accessibility.

Of course this leads to a sizable image. If you want to show a small
resolution version, simply add `{:.small}` after the image to get the
small version (300 pixels width):

```
![Abell 70](assets/abell70.jpg){:.small}
```

produces

![Abell 70](assets/abell70.jpg){:.small}


Many a time, you want to invert a sketch or an image, i.e. turn white-on-black into black-on-white. That's made easy too: just add `{:.invert}` after your image:

```
![Abell 70](assets/abell70.jpg){:.invert}{:.small}
```

produces

![Abell 70](assets/abell70.jpg){:.invert}{:.small}


For the above to work, the image must first be added to the `docs/assets/` folder in the
repository if referencing it locally as above. One can also instead
refer to an image that's on the internet,

```
![Hubble Rose](https://stsci-opo.org/STScI-01EVT4TTB262W6BBPYW37747W3.jpg){:.small}
```

The above fetches the image from the STScI website, as seen below:

`![Hubble Rose](https://stsci-opo.org/STScI-01EVT4TTB262W6BBPYW37747W3.jpg){:.small}


We also have `{:.tiny}` which sizes the width to 100 pixels:

```
![Hubble Rose](https://stsci-opo.org/STScI-01EVT4TTB262W6BBPYW37747W3.jpg){:.tiny}
```

results in

![Hubble Rose](https://stsci-opo.org/STScI-01EVT4TTB262W6BBPYW37747W3.jpg){:.tiny}

## For more

See the KramDown quick reference [here](https://kramdown.gettalong.org/quickref.html)