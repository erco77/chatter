#!/usr/bin/perl

$|=1;
use CGI;
use POSIX;              # strftime()
require "ctime.pl";
$ENV{TZ} = "PST8PDT";

# 
#    Erco Chatter - Simple multi-participant single conversation cgi-bin webchat (perl/javascript)
#    Copyright (C) 2012  Greg Ercolano.
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#


### CONFIGURATION GLOBALS -- YOU MUST CONFIGURE THESE vvv

# THE URL TO THIS SCRIPT
#     This is the url users use to reach the script
#
$G::selfurl = "http://seriss.com/cgi-bin/chat/chatter.cgi";

# THE CONVERSATION FILE
#    This file must exist (even if empty) and must be read/writable
#    to the apache user. Should be an absolute path.
#
$G::chatfile = "/usr/home/seriss/tmp/chatter.txt";

# THE CONVERSATION ARCHIVE FILE
#     When the moderator hits the 'Archive' button, the above chatter.txt
#     file is cleared, it's contents appeded to this chat archive file.
#
$G::chatarchive = "/usr/home/seriss/tmp/chatter-archive.txt";

# THE USERNAME OF THE MODERATOR
#     This user will have the 'archive' button visible to them.
# 
$G::moderator = "erco";

### END GLOBALS -- CONFIGURE THESE ^^^
###########################################################################

# MISC CONFIGURABLE GLOBALS
$G::refresh_secs     = 3;      # refresh update time (in seconds)
$G::idletimeout_mins = 20;     # warn if user idle for longer than #seconds (stops refreshing from server)

# LOGIN WINDOW COLORS
$G::login_bgcolor      = "#ffffff"; # login screen bgcolor

# CHAT WINDOW COLORS
$G::chat_bgcolor       = "#ffffff"; # chat bgcolor
$G::you_color          = "#777777"; # chat color for 'your' text
$G::them_color         = "#0000ff"; # chat color for 'their' text
$G::sysmsg_color       = "#ff0000"; # chat color for 'system messages' text

# 'SEND' WINDOW COLORS
$G::send_bgcolor       = "#dddddd"; # send input bgcolor
$G::send_field_bgcolor = "#ffffff"; # send input field bgcolor
$G::send_field_color   = "#000000"; # send input field text color

# DARK COLORS
# $G::you_color           = "#999999"; # chat color for 'your' text
# $G::them_color          = "#ddddff"; # chat color for 'their' text
# $G::sysmsg_color        = "#ff0000"; # chat color for 'system messages' text
# $G::login_bgcolor       = "#ffffff"; # login screen bgcolor
# $G::chat_bgcolor        = "#000000"; # chat bgcolor
# $G::send_bgcolor        = "#444444"; # send input bgcolor
# $G::send_field_bgcolor  = "#222222"; # send input field bgcolor
# $G::send_field_color    = "#999999"; # send input field text color

### SUBROUTINES

# SHOW AN ERROR IN BROWSER AND HTTP LOG, EXIT
sub Fatal($) {
    my ($msg) = @_;
    print "<PRE><B>$msg\n";
    print STDERR "$msg\n";
    exit(1);
}

sub ShowLogin() {
    print << "EOF";
<html>
<head><title>Erco Chatter: Login</title></head>
<style type='text/css'>
  body { 
    font-family: sans-serif,arial;
    background: ${G::login_bgcolor};
  }
</style>
<form method=post action=$G::selfurl?-login>
  Enter name to use for this chat:
  <input id=login_input  type=INPUT  name=Username VALUE=''>
  <input id=login_button type=SUBMIT name=Login    VALUE=Login>
</form>
</html>
<script>
      // Keep input field in focus
      document.getElementById("login_input").focus();
</script>
EOF
    return(0);
}

# SHOW SPLIT SCREEN
#    Chat script on top, input form below.
#
sub ShowFrames($) {
    my ($username) = @_;
    print << "EOF";
<html>
<head><title>Erco Chatter: $username</title></head>
<style type="text/css">
  body {
    font-family: sans-serif,arial;
    background: ${G::chat_bgcolor};
  }
</style>
<frameset rows="78%,22%">
  <frame src="$G::selfurl?-showchat+$username" NAME="CHATAREA">
  <frame src="$G::selfurl?-showform+$username" NAME="INPUTAREA">
  <noframes>No frames? Your browser is busted</noframes>
</frameset>
</html>
EOF
    return(0);
}

# SHOW BOTTOM CONTENTS OF CHATFILE
sub ShowChat($) {
    my ($username) = @_;
    print << "EOF";
      <html>
      <style type='text/css'>
        body {
          font-family: sans-serif,arial;
          background: ${G::chat_bgcolor};
        }
        /***** XXX: This causes trouble in Firefox for copy+paste..
                    white space isn't preserved in the paste. So we
                    insert a <pre> into the content instead.
        div.chat {
          font-family: monospace;
          white-space: pre;
        }
        ******/
      </style>
      <div id='Chat' class='chat'>[..loading chat file -- please wait..]</div>
      <script>
      var G_newchatsize  = -1;
      var G_chatsize     = -1;
      var G_idletime     = 0;
      var G_content_busy = 0;                   // ==1 while chat update is running
      var G_content_firsttime = 1;
      // Handle getting a URL's value via AJAX.
      //     Invokes callback 'cb' when the data is ready.
      //     This operation runs in the background.
      //
      function ProcessAjax(url,cb) {
          //document.getElementById("Chat").innerHTML += ("*** PROCESSAJAX CALLED: URL=" + url + "<BR>\\n");
          //document.getElementById("Chat").innerHTML += ("TIME="+Date.getTime()+"<br>\\n");
          //document.getElementById("Chat").innerHTML += ("URL='"+url+"'<br>\\n");
          if (window.XMLHttpRequest) {              // firefox/recent browsers
              req = new XMLHttpRequest();
              req.onreadystatechange = cb;          // set up callback for when operation completes
              try { req.open("GET", url, true); }
              catch (e) { alert(e); }
              // Need this for IE, but wrong for firefox (req.status returns 320 error)
              req.setRequestHeader("If-Modified-Since", "Fri,  1 Jan 1999 00:00:00 UTC"); // ensure no cache on IE
              req.send(null);
          } else if (window.ActiveXObject) {        // OLD IE
              req = new ActiveXObject("Microsoft.XMLHTTP");
              if ( req ) {
                  req.onreadystatechange = cb;      // set up callback for when operation completes
                  req.open("GET", url, true);
                  req.send();
              }
          } else {
              document.getElementById("Chat").innerHTML += ("ProcessAjax(): not available<br>\\n");
          }
      }
      // CHAT UPDATE -- STEP 2: UPDATE CHAT CONTENT
      function UpdateChatContent_CB() {
          if ( req.readyState == 4 ) {    // 4=DONE
              chatwin = document.getElementById("Chat");
              if ( G_content_busy ) {
                  if ( G_content_firsttime ) {
                      chatwin.innerHTML = "<pre>" +                     // clears previous '[loading chat]' msg, establish <pre> formatted text
                                          req.responseText +            // append new info
                                          "</pre>";                     // XXX: the browsers (oddly) add this if we don't.. so add now + remove later
                      G_content_firsttime = 0;
                  } else {
                      chatwin.innerHTML = chatwin.innerHTML.replace("</pre>","") +      // remove trailing </pre> - see XXX above
                                          req.responseText;             // append new info
                  }
                  if ( document.documentElement.clientHeight > 0 ) {
                      window.scrollTo(0, document.documentElement.clientHeight); // Firefox/Safari: scroll to bottom
                  } else {
                      window.scrollTo(0, chatwin.scrollHeight);                  // IE8
                  }
                  G_content_busy = 0;
                  G_chatsize = G_newchatsize;
              }
          } else {
              chatwin = document.getElementById("Chat");
              //chatwin.innerHTML += "UpdateChatContent_CB(): readyState=" + req.readyState + "<br>\\n";
          }
      }
      // CHAT UPDATE -- STEP 1: GET SIZE OF CHAT FILE
      //     If size is different, set up an chatfile update
      //
      function GetChatSize_CB() {
          var now = new Date();
          if ( G_idletime == 0 ) { G_idletime = now; }

          //// if ( req.status != 200 ) { alert("Problem: " + req.statusText); } // DOESNT WORK IN IE
          //document.getElementById("Chat").innerHTML += ("REQSTATUS/READYSTATE=" + req.status + ","+req.readyState+" -- text='" + req.responseText+"'<br>\\n");
          if ( req.readyState == 4 ) {    // 4=DONE
              arr = req.responseText.match(/size=(\\d+)/);
              //document.getElementById("Chat").innerHTML += ( "ARR=" + arr );
              if ( arr == undefined || arr[1] == undefined ) {
                  // Error? Perhaps they sent us an 'error=xxx' instead.
                  document.getElementById("Chat").innerHTML += "<B><FONT COLOR=RED>[SYSTEM ERROR: " +
                                                               req.responseText + "]</FONT></B><BR>";
              } else {
                  G_newchatsize = arr[1]
                  //document.getElementById("Chat").innerHTML += ("NEW="+G_newchatsize+",OLD="+G_chatsize+", BUSY? " + G_content_busy + "<BR>");
                  if ( G_newchatsize != G_chatsize ) {
                      // Chat file size changed? Update content window with new data
                      if ( G_content_busy == 0 ) {
                        G_content_busy = 1;
                        ProcessAjax('${G::selfurl}?-getchat+$username+'+G_chatsize, UpdateChatContent_CB);
                      }
                      // Reset idle time to now
                      G_idletime = now;
                  } else {
                      // No change -- check for idle timeout
                      var idlemins = (now - G_idletime) / 1000 / 60;
                      if ( idlemins > ${G::idletimeout_mins} ) {
                          alert("You've been idle for ${G::idletimeout_mins} minutes.\\n"+
                                "Click OK to continue session. Please logout if you're done.");
                          G_idletime = 0;               // reset to zero
                      }
                  }
              }
          }
          return true;
      }
      // Update the chat page for the first time
      //     Set up an AJAX operation to get the data and display it.
      //
      function UpdateChat(url) {
          // Don't check size if content callback still running..
          // (content might take longer to load than our interval)
          //
          if ( !G_content_busy ) {
              ProcessAjax('${G::selfurl}?-getchatsize+$username', GetChatSize_CB);
          }
      }
      UpdateChat();
      setInterval("UpdateChat();", ${G::refresh_secs} * 1000);
      </script>
EOF
}

sub GetChat($$) {
    my ($username,$seekpos) = @_;
    unless(open(FD,"<${G::chatfile}"))
         { Fatal("${G::chatfile}: $!"); }
    if ($seekpos > 0) { seek(FD, $seekpos, 0); }
    my $snipuser = "";
    while ( <FD> ) {
        s/[\r\n]*//g;
        s/&/\&amp;/g;
        s/>/\&gt;/g;
        s/</\&lt;/g;
        if    ( /^$username: --- snip \(start\)$/ ) { $snipuser = $username; }
        elsif ( /^$username: --- snip \(end\)$/   ) { $snipuser = ""; }
        if ( /^$username:/ || $snipuser eq $username ) {
            # YOU
            print("<font color=${G::you_color}>$_</font>\n");
        } elsif ( /^--- (.*' has joined the chat|.*has logged out$)/ ) {
            # MACHINE MESSAGE
            print("<font color=${G::sysmsg_color}>$_</font>\n");
        } elsif ( /^--- TIME MARK:/ ) {
            # TIME MARK
            print("<font color=orange><br>$_</br></font>\n");
        } else {
            # THEM
            print("<font color=${G::them_color}>$_</font>\n");
        }
    }
    close(FD);
}

sub GetChatSize($) {
    my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,
        $atime,$mtime,$ctime,$blksize,$blocks) = stat($_[0]);
    if ( !defined($size) ) { return(-1); }
    else { return($size); }
}

# RETURN MTIME FOR FILE
sub StatMtime($) {
    my @arr = stat($_[0]);
    if ( $#arr == -1 ) { print STDERR "stat('$_[0]'): $!\n"; return(0); }
    else               { return($arr[9]); }   # mtime
}

# CHECK IF IT'S TIME TO SHOW A TIME MARK
#     Every 15 mins..
#
sub TimeMarkCheck() {
    $ENV{TZ} = "PST8PDT";
    my $mtime = StatMtime(${G::chatfile});
    my $lasthour = POSIX::strftime("%H",localtime($mtime));
    my $thishour = POSIX::strftime("%H",localtime(time()));
    my $lastmin  = POSIX::strftime("%M",localtime($mtime));
    my $thismin  = POSIX::strftime("%M",localtime(time()));
    return( (($lasthour != $thishour) || (int($lastmin/15) != int($thismin/15))) ? 1 : 0);
}

# HANDLE NEW TEXT POSTING, APPEND TO CHATFILE
sub Post($) {
    my ($username) = @_;
    my $cgi = new CGI();
    my $send = $cgi->param("Send");
    my $text = $cgi->param("Text");
    if ( $text !~ /\n$/ ) { $text .= "\n"; }
    unless(open(FD, ">>${G::chatfile}")) { Fatal("${G::chatfile}: $!"); }
    if ( $cgi->param("Logout") eq "Logout" ) {
        print "<h2>$username: you have logged out.</h2>\n";
        syswrite(FD,"\n--- $username has logged out\n\n");
        close(FD);
        exit(0);
    }
    if ( $cgi->param("Archive") eq "Archive" && $username eq $G::moderator ) {
        close(FD);
        unless(open(IN, "<${G::chatfile}")) { Fatal("${G::chatfile}: $!"); }
        unless(open(OUT, ">>${G::chatarchive}")) { Fatal("${G::chatarchive}: $!"); }
        print OUT "=== ARCHIVED " . ctime(time());
        while ( <IN> ) { print OUT $_; }
        close(IN);
        close(OUT);
        unless(open(EMPTY, ">${G::chatfile}")) { Fatal("${G::chatfile}: $!"); }
        close(EMPTY);
        print "<h4><font color=green>Archive successful</font></h4>";
        exit(0);
    }
    if ( TimeMarkCheck() ) {
        syswrite(FD, "--- TIME MARK: ".ctime(time())."\n");
    }
    if ( $send ne "Send" ) {
        syswrite(FD,"$username: --- snip (start)\n");
    }
    foreach ( split(/\n/, $text ) ) {
        if ( $send eq "Send" ) { syswrite(FD,"$username: $_\n"); }
        else                   { syswrite(FD,"$_\n"); }
    }
    if ( $send ne "Send" ) {
        syswrite(FD,"$username: --- snip (end)\n");
    }
    close(FD);
    if ( $cgi->param("Logout") eq "Logout" ) { exit(0); }
}

# PRESENT INPUT TEXT FIELD TO USER WITH 'SEND' BUTTON
sub ShowInputForm($)
{
    my ($username) = @_;
    print <<"EOF";
<html>
<style type='text/css'>
  body {
    font-family: sans-serif,arial;
    background: ${G::send_bgcolor};
  }
  .chatinput {
      font-family: monospace;
      font-size: 14;
      color: ${G::send_field_color};
      background: ${G::send_field_bgcolor};
  }
</style>
<script>
    // Enable the 'tab' key in the 'textarea'
    var tab = "\\t";
    function CatchTab(evt) {
        var t = evt.target;
        var ss = t.selectionStart;
        var se = t.selectionEnd;
        // Detect tab only (not shift-tab, so reverse key nav can work)
        if (evt.keyCode == 9 && !event.shiftKey ) {
            evt.preventDefault();
            // Special case of multi line selection
            if (ss != se && t.value.slice(ss,se).indexOf("n") != -1) {
                // In case selection was not of entire lines (e.g. selection begins in the middle of a line)
                // we ought to tab at the beginning as well as at the start of every following line.
                var pre = t.value.slice(0,ss);
                var sel = t.value.slice(ss,se).replace(/n/g,"n"+tab);
                var post = t.value.slice(se,t.value.length);
                t.value = pre.concat(tab).concat(sel).concat(post);
                t.selectionStart = ss + tab.length;
                t.selectionEnd = se + tab.length;
            } else {
                // "Normal" case (no selection or selection on one line only)
                t.value = t.value.slice(0,ss).concat(tab).concat(t.value.slice(ss,t.value.length));
                if (ss == se) {
                    t.selectionStart = t.selectionEnd = ss + tab.length;
                } else {
                    t.selectionStart = ss + tab.length;
                    t.selectionEnd = se + tab.length;
                }
            }
        }
    }
</script>
<body>
  <table><tr>
    <td align=left><font color=#Aaa>You are $username</font></td>
    <form method=post action=$G::selfurl?-post+$username target=_top>
    <td align=right> <input type=SUBMIT name=Logout VALUE='Logout'> </td>
EOF
    if ( $username eq $G::moderator ) {
        print <<"EOF";
    <td align=right> <input type=SUBMIT name=Archive VALUE='Archive'> </td>
EOF
    }

    print <<"EOF";
    </form>
  </tr><tr>
    <form method=post action=$G::selfurl?-post+$username>
      <td colspan=2>
        <!-- CHAT INPUT FIELD -->
        <textarea cols=100 
                  rows=4
                  id=TextId
                  name=Text
                  class=ChatInput
                  onkeydown="CatchTab(event);"></textarea>
      </td>
    </tr><tr>
        <td align=left > <input type=SUBMIT name=Send VALUE=Send></td>
        <td align=right> <input type=SUBMIT name=SendCode VALUE='Send code'></td>
    </tr>
    </form>
  </table>
  <script>
      // Keep input field in focus
      document.getElementById("TextId").focus();
  </script>
EOF
    return(0);
}

# LOG THAT SOMEONE HAS JOINED THE CHAT
sub Joined($) {
    my ($username) = @_;
    unless(open(FD, ">>${G::chatfile}")) { Fatal("${G::chatfile}: $!"); }
    syswrite(FD,"\n--- '$username' has joined the chat " . ctime(time()) . "\n");
    close(FD);
}

# HANDLE A NEW LOGIN
sub HandleLogin() {
    my $cgi = new CGI();
    my $username = $cgi->param("Username");
    $username =~ s/\s+//g;
    $username = substr($username,0,14);
    if ( length($username ) == 0 ) {
        print "<FONT COLOR=RED><B>Error: you gave an empty username.</B></FONT><BR>".
              "Click <a href='$G::selfurl'>here</a> to go to the login page and enter a valid username.";
        return(0);
    }
    Joined($username);
    ShowFrames($username);
    return(0);
}

### MAIN
{

    # MAKE SURE CHATFILE HAS CONTENTS
    if ( ! -e ${G::chatfile} ) {
        open(FD, ">${G::chatfile}");
        print FD "Started " . ctime(time());
        close(FD);
    }

    # WHAT TO SHOW IF NO FLAGS SPECIFIED
    if ( ! defined($ARGV[0]) ) {
        print "Content-type: text/html\n\n";
        ShowLogin();
        exit(0);
    }

    # WHAT TO SHOW IF NO FLAGS SPECIFIED
    if ( $ARGV[0] eq "-login" ) {
        print "Content-type: text/html\n\n";
        HandleLogin();
        exit(0);
    }

    # WHAT TO SHOW IF NO FLAGS SPECIFIED
    if ( $ARGV[0] eq "-splitscreen" ) {
        my $username = (defined($ARGV[1])) ? $ARGV[1] : "???";
        print "Content-type: text/html\n\n";
        ShowFrames($username);
        exit(0);
    }

    # SHOW CHAT WINDOW
    if ( $ARGV[0] eq "-showchat" ) {
        my $username = (defined($ARGV[1])) ? $ARGV[1] : "???";
        print "Content-type: text/html\n\n";
        ShowChat($username);
        exit(0);
    }

    # DUMP CHAT FILE
    #    AJAX function calls this if it knows chat file changed in size
    #    and needs to be updated.
    #
    if ( $ARGV[0] eq "-getchat" ) {
        my $username = (defined($ARGV[1])) ? $ARGV[1] : "???";
        my $seekpos  = (defined($ARGV[2])) ? $ARGV[2] : -1;
        print "Content-type: text/html\n\n";
        GetChat($username, $seekpos);
        # print("USERNAME=$username, SEEK=$seekpos<BR>\n");
        exit(0);
    }

    # RETURN CHAT FILE SIZE
    #    AJAX function calls this to see if chatfile changed in size..
    #
    if ( $ARGV[0] eq "-getchatsize" ) {
        print "Content-type: text/plain\n\n";
        my $size = GetChatSize(${G::chatfile});
        if ( $size < 0 ) {
            print "error: ${G::chatfile}: $!\n";
        } else {
            print "size=$size\n";
        }
        exit(0);
    }

    # SHOW THE INPUT FORM (BOTTOM HALF OF CHAT SCREEN)
    if ( $ARGV[0] eq "-showform" ) {
        my $username = (defined($ARGV[1])) ? $ARGV[1] : "???";
        print "Content-type: text/html\n\n";
        ShowInputForm($username);
        exit(0);
    }

    # HANDLE A TEXT POSTING
    if ( $ARGV[0] eq "-post" ) {
        print "Content-type: text/html\n\n";
        my $username = (defined($ARGV[1])) ? $ARGV[1] : "???";
        Post($username);
        ShowInputForm($username);
        exit(0);
    }

    exit(0);
}

