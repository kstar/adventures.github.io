---
layout: or
title: Example Observing Report
author: Akarsh Simha
---

This is an example of how the simple "markup" language called MarkDown
can be used to create observing reports on Adventures in Deep
Space. There are many MarkDown tutorials on the internet, but we have
our own intro, see [here](example.html).

## Preamble

Observing report pages start with a "Front Matter", which contains the following format:

```
---
layout: or
title: <Title of your OR>
author: <Your Name>
---
```

The title should not contain the "Adventures in Deep Space", doing
that in the page title is taken care of by our HTML generation
engine. It should contain OR and the date of your OR.

## Horizontal dividers

After typing out each object, you may want a dividing line. Simply type:
```
----
```
to get a dividing line, like below.

----

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

----

## Links

A link can be added by putting square brackets around the text and putting the URL in parantheses:
```
Also check out the [Deep Sky Forum](https://deepskyforum.com)
```
produces the following:

Also check out the [Deep Sky Forum](https://deepskyforum.com)

----

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

Images in OR mode are centered by default. To center text, place it
within `<center>` tags:

```
<center>
This is some centered text
</center>
```

produces:

<center>
This is some centered text
</center>
## For more

See the KramDown quick reference [here](https://kramdown.gettalong.org/quickref.html)
