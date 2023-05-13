window.addEventListener('load', function() {
    const showRestorePointsButton = document.querySelector('#show-restore-points-button');
    const restorePointsContainer = document.querySelector('#restore-points-container');
    const restoreForm = document.querySelector('#restore-form');
    const restorePointsTable = document.querySelector('#restore-points-table');
    const noRestorePointsMessage = document.createElement('p');
    noRestorePointsMessage.textContent = 'No restore points, create one!';
    restorePointsContainer.appendChild(noRestorePointsMessage);

    let restorePointsVisible = false;

    showRestorePointsButton.addEventListener('click', function() {
        if (restorePointsVisible) {
            restorePointsContainer.style.display = 'none';
            showRestorePointsButton.textContent = 'Show restore points';
            restorePointsVisible = false;
        } else {
            fetch('/restore/')
                .then(response => response.json())
                .then(data => {
                    while (restorePointsTable.rows.length > 1) {
                        restorePointsTable.deleteRow(1);
                    }

                    if (data.length === 0) {
                        noRestorePointsMessage.style.display = 'block';
                        restorePointsTable.style.display = 'none';
                    } else {
                        noRestorePointsMessage.style.display = 'none';
                        restorePointsTable.style.display = 'table';

                        for (const item of data) {
                            const row = document.createElement('tr');
                            row.addEventListener('click', function() {
                                restoreForm.action = `/restore/${item.filename}/`;
                                restoreForm.submit();
                            });

                            const restorePointCell = document.createElement('td');
                            restorePointCell.classList.add('row');
                            restorePointCell.textContent = item.filename;
                            row.appendChild(restorePointCell);

                            const actionCell = document.createElement('td');
                            const deleteButton = document.createElement('button');
                            deleteButton.classList.add('delete-button');
                            deleteButton.textContent = '🗑️';
                            deleteButton.addEventListener('click', function(event) {
                                event.stopPropagation();
                                fetch(`/delete_restore_point/${item.filename}/`, {method: 'POST'})
                                    .then(response => {
                                        if (response.ok) {

                                            row.remove();
                                        }
                                    });
                            });
                            actionCell.appendChild(deleteButton);
                            row.appendChild(actionCell);

                            restorePointsTable.appendChild(row);
                        }
                    }

                    restorePointsContainer.style.display = 'block';
                    showRestorePointsButton.textContent = 'Hide restore points';
                    restorePointsVisible = true;
                });
        }
    });
});