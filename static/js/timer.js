$(document).ready(function () {
    // timer function
    function startTimer(duration, display, btn) {
        var timer = duration, minutes, seconds;
        var refresh = setInterval(function () {
            minutes = parseInt(timer / 60, 10)
            seconds = parseInt(timer % 60, 10);

            minutes = minutes < 10 ? "0" + minutes : minutes;
            seconds = seconds < 10 ? "0" + seconds : seconds;

            var output = minutes + " : " + seconds;
            display.text(output);
            $("title").html(output + " - 番茄钟");

            if (--timer < 0) {
                display.text("Time's Up!");
                btn.text("休息");
                btn.attr("href", "/pomodoro?rest")
                clearInterval(refresh);  // exit refresh loop
                var music = $("#over_music")[0];
                // music.play();
                alert("Time's Up!");
            }
        }, 1000);

    }

    // start timer
    jQuery(function ($) {
        var display = $('#time');
        var btn = $('#btn_cancel');
        startTimer(Seconds, display, btn);
    });

    // show help information
    $('#help-info').hide();
    $('#help-btn').hover(function () {
        $('#help-info').toggle();
    });
})