

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('subforum-search');
    const resultsContainer = document.getElementById('search-results');


    if (!searchInput || !resultsContainer) return;

    searchInput.addEventListener('input', () => {
        const query = searchInput.value.trim();
        resultsContainer.innerHTML = '';

        if (query.length < 3){
            resultsContainer.classList.add('d-none');
            return;
        }
        fetch(`/ajax/search_subforums?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
            if (data.length === 0) {
                resultsContainer.classList.remove("d-none");
                resultsContainer.innerHTML = '<li class="list-group-item text-muted"> Inga SubForum hittades!</li>';
                return;
            }

            resultsContainer.classList.remove("d-none");

            const seen = new Set();

            data.forEach(forum => {
                const name = forum.name.toLowerCase();
                if (seen.has(name)) return;
                seen.add(name);

                const item = document.createElement('li');
                item.className = 'list-group-item';
                item.innerHTML =
                    `<a href="/subforum/${forum.name}"class="text-decoration-none">${forum.name}</a>`;
                    resultsContainer.appendChild(item);
            });
        });
    });
        document.addEventListener('click', (event) => {
            if (!searchInput.contains(event.target) && !resultsContainer.contains(event.target)) {
                resultsContainer.classList.add('d-none');
            }
            });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
            resultsContainer.classList.add('d-none');
            }
        });
    });