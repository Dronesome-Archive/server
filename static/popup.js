function show_popup(id) {
    // Get DOM object
    let popup = document.getElementById('id');
    if (!popup || popup.style.getPropertyValue('visibility')==='visible') return;

    // Hide others
    for (const other in document.getElementsByClassName('popup')) hide_popup(other.id);

    // Create background
    let bg = document.createElement('div');
    bg.onclick = () => hide_popup(id);
    bg.classList.add('popup_background');
    document.getElementsByClassName('body')[0].appendChild(bg);

    // Show popup
    popup.style.setProperty('visibility', 'visible');
}

function hide_popup(id) {
    // Get DOM object
    let popup = document.getElementById('id');
    if (!popup || popup.style.getPropertyValue('visibility')==='hidden') return;

    // Remove background
    for (const bg in document.getElementsByClassName('popup_background')) document.removeChild(bg);

    // Hide popup
    popup.style.setProperty('visibility', 'hidden');
}