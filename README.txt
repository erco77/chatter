Erco Chatter - Simple multi-participant online web chat (perl/javascript)
               1.10 Greg Ercolano.

OVERVIEW
    This is a simple to configure webchat cgi-bin script you can install on
    your webserver to allow multiple users to login and 'chat' with each
    other. Tested with IE8, Firefox, and Safari.

    It is a single script to keep installation and maintenance simple.
    The script manages only one file, the 'chatter.txt' file, which 
    contains the 'current conversation' text.

    Multiple users can login with usernames and chat amongst each other.
    Only a single conversation is managed, and all the content is appended
    to the chatter.txt file, which all the other browsers watch for changes
    and update their screens when the file size changes.
    
    This script does not manage multiple conversations or 'channels'; 
    there is only a single conversation that many people can join.
    The moderator can "archive" the conversation at the end, which 
    'clears the slate' so a new, empty chat window is ready for the
    next session.

    However, you can make separate chat sessions with this script by making
    separate copies of the chat script so that each has its own URL, and just
    modify the chatter.txt filename each manages. Then users can have separate
    concurrent conversations, a separate URL and conversation file for each.

    A fixed width font is used throughout so that code pastes and indenting
    maintains alignment. This allows pasting code without screwing up
    indenting (a big problem with most chat tools) There is also a special
    "Send Code" button that pastes text into the chat without user prompts
    on each line, making it easy to let others copy/paste the code.

INSTALLATION
    To install, drop the script in your cgi-bin directory, and customize these
    four global variables at the top of the chatter.cgi script as appropriate
    for your web server setup:

1) $G::selfurl = "http://seriss.com/cgi-bin/chat/chatter.cgi";

      This is the URL to the script on your web server, i.e.
      the url users use to reach the script.

2) $G::chatfile = "/usr/home/seriss/tmp/chatter.txt";

      The chat conversation file.
  
      This file must exist (even if empty) and must be read/writable
      to the apache user. Should be an absolute path.
  
      Each time a user types a comment, it gets appended to this file.
      The other browsers test this file for file size changes, and
      when triggered, causes an update.

3) $G::chatarchive = "/usr/home/seriss/tmp/chatter-archive.txt";

      The archive file.
  
      When the moderator hits the 'Archive' button, the above chatter.txt
      file is cleared, it's contents appeded to this chat archive file.

4) $G::moderator = "erco";

      The username of the moderator.
  
      This user will have the 'archive' button visible to them.

HOW IT WORKS
    Once you login, the browser is split into two frames;
    the chat history at the top, and the input field at the bottom.
    
    The chat file's contents is fetched via a javascript call,
    and is written into the upper chat history window. The browser
    then sets a 5 second timer to check the chat file's size 
    every 5 seconds to see if it's increased in size. If so, 
    the new contents is appended to the browser's chat history window.
    
    Whenever someone enters new text and hit's "Send", the form
    is posted to the server, which appends the new text to the 
    chat file.  Within a few seconds, all the browsers will see 
    the chat file's size has changed, and will update their 
    chat screens with the new text.
    
    The polling speed default is 5 seconds. This speed can be
    changed by modifying the refresh_msecs global at the top 
    of the script. A faster polling speed makes updates quicker,
    but induces more load on the network and server.
    
SECURITY
    The script has no security of its own; anyone can connect
    to it, there's no password system.

    If you want to password protect the script, you can use
    normal .htaccess / htpasswd files to manage access.

MAINTENANCE
    The chatter.txt file keeps track of the running conversation.

    Since it never zeroes itself out, if you want to clear the chat,
    the moderator can use the 'Archive' button at the end of the
    conversation, or a sysadmin can simply empty the file by just
    zeroing out the chatter.txt file, e.g.

        sleep 0 > chatter.txt
    
DOWNLOAD
    You can download the latest version of this program from:
    http://seriss.com/people/erco/unixtools/chatter/

LICENSE
    This is GPL licensed software.
    See COPYING file for license.
