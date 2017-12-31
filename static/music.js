var ws = io.connect('//' + document.domain + ':' + location.port);
var song = null;
var loading = $('#loading');
loading.hide();
var messages = $('#messages2');
messages.hide();

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
            $('#queue').append(t.name + ' - ' + t.artists[0].name + '<a class="songvote" id="upvote-' + t.uri + '" title="Upvote"><span class="fa fa-thumbs-up"></span></a><a id="downvote-' + t.uri + '" title="Downvote" class="songvote text-danger"><span class="fa fa-thumbs-down"></span></a><span id="' + t.uri.split(':')[2] + '">' + votes + '</span><br>');
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
    console.log(vspan.html() + " " + val);
    if (v[0] == 'upvote')
        vspan.html(val += 1);
    else if (v[0] == 'downvote')
        vspan.html(val -= 1);
    ws.emit('vote', {uri: v[1], vote: v[0]});
});

$('#search').on('input', function () {
    loading.fadeIn();
    ws.emit('search', {
        query: $('#search').val()
    });
});

ws.on('search results', function(songs) {
    $('#results').empty();
    songs.forEach(function (s) {
        $('#results').append('<button class="btn btn-info btn-block song-result" id="' + s.uri + '">' + s.name + ' - ' + s.artists[0].name + '</button>');
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

$('#results').on('click', '.song-result', function () {
    ws.emit('request', {
        uri: $(this).attr('id')
    });
});

$('.ctl').on('click', function() {
    ws.emit('admin', {action: $(this).attr('id')});
});

function refresh() {
    ws.emit('refresh');
}

refresh();
setInterval(refresh, 5000);
setTimeout(function() {
    $('#messages').fadeOut();
}, 5000);
