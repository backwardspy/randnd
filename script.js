var last_few = [];

function regen(type) {
    fetch(`http://localhost:8000/${type}`).then(function (response) {
        response.json().then(function (data) {
            add_phrase(data.phrase);
        });
    });
}

function add_phrase(phrase) {
    last_few.push(phrase);
    if (last_few.length > 10) {
        last_few.shift();
    }
    render();
}

function render() {
    document.getElementById("phrase").innerText = last_few[last_few.length - 1];

    var last_phrases = document.getElementById("last-phrases");
    last_phrases.innerHTML = "";

    for (var i = last_few.length - 2; i >= 0; i--) {
        var li = document.createElement("li");
        li.innerText = last_few[i];
        li.style.opacity = 0.2 + (1 - (last_few.length - i) / 10);
        last_phrases.appendChild(li);
    }
}
