document.querySelectorAll('.update-button').forEach(function(button) {
    button.addEventListener('click', function() {
        var gameId = this.getAttribute('data-id');
        var form = document.querySelector('.update-form[data-id="' + gameId + '"]');
        form.style.display = 'table-row';
    });
});