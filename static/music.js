var ws = io.connect('//' + document.domain + ':' + location.port);
var song = null;
var loading = $('#loading');
loading.hide();
var messages = $('#messages2');
messages.hide();
var typingTimer;                //timer identifier
var doneTypingInterval = 300;  //time in ms, 5 second for example
var search = $('#search');

ws.on('msg', function(data) {
    messages.attr('class', 'alert alert-' + data.class);
    messages.html(data.msg);
    messages.fadeIn();
    setTimeout(function() {
        messages.fadeOut();
    }, 5000);
});

ws.on('track', function(data) {
    song = data;
    $('#song-title').html(song.title);
    $('#song-artist').html(song.artists);
    $('#album-art').attr('src', song.art);
});

ws.on('tracks', function(tracks) {
    $('#queue').empty();
    tracks.forEach(function (t) {
        if (t != null) {
            t = t.track;
            var votes = t.votes != undefined ? t.votes : 0;
            $('#queue').append(t.name + ' - ' + t.artists[0].name + '<a hidden class="songvote" id="upvote-' + t.uri + '" title="Upvote"><span class="fa fa-thumbs-up"></span></a><a hidden id="downvote-' + t.uri + '" title="Downvote" class="songvote text-danger"><span class="fa fa-thumbs-down"></span></a><span hidden id="' + t.uri.split(':')[2] + '">' + votes + '</span><br>');
        }
    });
});

ws.on('requests', function(requests) {
    $('#requests').empty();
    requests.forEach(function (t) {
        $('#requests').append(t.title + ' - ' + t.artist + '<a class="songvote" id="upvote-' + t.uri + '" title="Upvote"><span class="fa fa-thumbs-up"></span></a><a id="downvote-' + t.uri + '" title="Downvote" class="songvote text-danger"><span class="fa fa-thumbs-down"></span></a><span id="' + t.uri.split(':')[2] + '">' + t.votes + '</span><br>');
    });
});

$(document).on("click", '.songvote', function(a) {
    var v = $(this).attr('id').split('-');
    var vspan = $('#' + v[1].split(':')[2]);
    var val = parseInt(vspan.html());
    if (v[0] == 'upvote')
        vspan.html(val += 1);
    else if (v[0] == 'downvote')
        vspan.html(val -= 1);
    ws.emit('vote', {uri: v[1], vote: v[0]});
});

//on keyup, start the countdown
search.on('keyup', function () {
  clearTimeout(typingTimer);
  typingTimer = setTimeout(do_search, doneTypingInterval);
});

//on keydown, clear the countdown
search.on('keydown', function () {
  clearTimeout(typingTimer);
});

function do_search() {
    if (search.val() != "") {
        loading.fadeIn();
        ws.emit('search', {
            query: search.val()
        });
    } else {
        $('#results').empty();
        loading.fadeOut();
    }
}

ws.on('search results', function(songs) {
    $('#results').empty();
    songs.forEach(function (s) {
        var artists = "";
        s.artists.forEach(function(a) {
            if (artists != "")
               artists += ", "
            artists += a.name;
        });
        $('#results').append('<button class="btn btn-info btn-block song-result" id="' + s.uri + '">' + s.name + ' - ' + artists + '</button>');
    });
    loading.fadeOut();
});

ws.on('disconnect', function () {
    $('#status_u').html('Status: <span class="text-danger">Disconnected</span>');
});

ws.on('connect', function () {
    $('#status_u').html('Status: <span class="text-success">Connected</span>');
    ws.emit('refresh');
});

ws.on('chatcount', function(data) {
    $('#chatcount').text(data);
});

$('#results').on('click', '.song-result', function () {
    ws.emit('request', {
        uri: $(this).attr('id')
    });
});

$('.ctl').on('click', function() {
    ws.emit('admin', {action: $(this).attr('id')});
});

$('#play_playlist').click(function() {
    ws.emit('admin', {
        action: 'playlist',
        uri: $('#playlist').val()
    });
});

var chat = $('#chat-messages');
var chatmsg = $('#chat-msg');
var message_count = 0;

ws.on('chat msg', function(data) {
    var username = '<span class="text-primary">' + data.username + ": " + '</span>';
    chat.append('<p>'+ username + data.message + '</p>');
    message_count++;
    if (message_count > 14) {
        chat.find('p:first').remove();
    }
});

$('#chat-div').keypress(function(e) {
    if(e.which == 13 && chatmsg.val() != "") {
        ws.emit('chat', {message: chatmsg.val()});
        chatmsg.val('');
    }
});

function refresh() {
    ws.emit('refresh');
}

refresh();
setInterval(refresh, 1000);
setTimeout(function() {
    $('#messages').fadeOut();
}, 5000);
