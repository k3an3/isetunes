var ws = io.connect('//' + document.domain + ':' + location.port);
var song = null;
var loading = $('#loading');
loading.hide();

ws.on('track', function (data) {
    song = data;
    $('#song-title').html(song.title);
    $('#song-artist').html(song.artists);
    $('#album-art').attr('src', song.art);
});

ws.on('tracks', function(tracks) {
    $('#queue').empty();
    console.log(tracks);
    tracks.forEach(function (t) {
        $('#queue').append('<button class="btn btn-info btn-block" id="' + t.uri + '">' + t.name + ' - ' + t.artists[0].name + '</button>');
    });
});

$('#search').on('input', function () {
    loading.fadeIn();
    ws.emit('search', {
        query: $('#search').val()
    });
});

ws.on('search results', function (songs) {
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
    console.log(this);
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
