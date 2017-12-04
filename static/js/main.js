(function (w, d, $) {
    // Remove the message shown on clicking close button.
    $(d)
        .on('click', '.message .fa-close', function () {
            $(this).parent().remove();
        });
})(window, document, jQuery);
