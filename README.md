# DevDocs Shell

A shell for [DevDocs](http://devdocs.io).

![Screenshot](http://i.imgur.com/W6Iw0ux.png)
![Screenshot](http://i.imgur.com/HL1zdXB.png)
![Screenshot](http://i.imgur.com/wSUny4b.png)

## Motivation

I liked [DevDocs](http://devdocs.io) and wanted to use it from
[VIM](http://www.vim.org). I've tried browser automation with Chromium
and separate profile with `--remote-shell-port`, but that didn't work
out so I made this script.

## Prerequisites

* Python 2.7+ or 3+
* WebKit2Gtk
* Gtk3 along with Python bindings (the new ones: GObject Inrospection)

## Usage

Just run `devdocs.py`. If you provide an argument then first argument
will be searched (all other arguments are ignored).

## VIM integration

Just add this to your .vimrc:

```
command! -nargs=? DevDocs :call system('devdocs.py <args> &')

au FileType python,ruby,javascript,html,php,eruby,coffee nmap <buffer> K :exec "DevDocs " . fnameescape(expand('<cword>'))<CR>

```

You'll have a command `DevDocs` and supported languages with use it for
providing help (K in normal mode, usually runs `man`).

**NOTE:** `devdocs.py` doesn't go to background hence one needs to use
`&` (shell background job) and its not supported on Win32.

## TODO

* After https://bugs.webkit.org/show_bug.cgi?id=127410 make sure HTML5
database is in app config directory.
* Maybe add tabs to open multiple terms?
