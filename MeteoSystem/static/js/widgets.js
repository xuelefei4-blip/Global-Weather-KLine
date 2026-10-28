(function () {
    const defaultStories = [
        {
            tag: "Montana Cold Wave",
            title: "Drop 54.4°C in 24h",
            summary: "1972 Loma, MT recorded world-record drop from 12.2°C to -42.2°C in 24 hours.",
            url: "https://en.wikipedia.org/wiki/United_States_temperature_extremes"
        },
        {
            tag: "Chinook Surge",
            title: "Surge 27°C in 2 Mins",
            summary: "1943 Spearfish, SD saw rapid temperature rise from -20°C to +7°C in just two minutes.",
            url: "https://en.wikipedia.org/wiki/Spearfish,_South_Dakota"
        },
        {
            tag: "Volcanic Winter",
            title: "Year Without Summer",
            summary: "1816 Tambora eruption caused severe global chill, bringing July snow to North America.",
            url: "https://en.wikipedia.org/wiki/Year_Without_a_Summer"
        },
        {
            tag: "Death Valley",
            title: "Peak Heat: 56.7°C",
            summary: "Death Valley recorded 56.7°C, the highest ambient air temperature ever on Earth.",
            url: "https://en.wikipedia.org/wiki/Furnace_Creek,_California"
        }
    ];

    function buildCard(story) {
        if (!story) return '';
        return `
            <div class="hook-card">
                <a href="${story.url}" target="_blank" class="hook-title" title="Open in Wikipedia">${story.title} ➔</a>
                <p>${story.summary}</p>
            </div>`;
    }

    function renderList(stories) {
        if (!Array.isArray(stories) || stories.length === 0) return;
        const leftContainer = document.querySelector('.side-slot-left .slot-content');
        const rightContainer = document.querySelector('.side-slot-right .slot-content');

        if (leftContainer) {
            leftContainer.innerHTML = buildCard(stories[0]) + buildCard(stories[1]);
        }
        if (rightContainer) {
            rightContainer.innerHTML = buildCard(stories[2]) + buildCard(stories[3]);
        }
    }

    function setupChatModal() {
        const openBtn = document.getElementById('open-chat-modal-btn');
        const overlay = document.getElementById('chat-modal-overlay');
        const closeBtn = document.getElementById('close-chat-modal-btn');
        const frame = document.getElementById('chat-embed-frame');

        if (!openBtn || !overlay) return;

        function openModal() {
            if (frame && frame.src === 'about:blank') {
                const src = frame.getAttribute('data-src');
                if (src) frame.src = src;
            }
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function closeModal() {
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        }

        openBtn.addEventListener('click', openModal);
        if (closeBtn) closeBtn.addEventListener('click', closeModal);

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closeModal();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && overlay.classList.contains('active')) {
                closeModal();
            }
        });
    }

    function init() {
        setupChatModal();

        // 1. 立即加载默认精炼数据，防止任何网络延迟或跨域导致空白
        renderList(defaultStories);

        // 2. 尝试拉取本地生成的 stories.json 进行实时动态覆盖
        fetch('static/data/stories.json?t=' + Date.now())
            .then(res => {
                if (!res.ok) throw new Error('Status ' + res.status);
                return res.json();
            })
            .then(remoteStories => {
                if (Array.isArray(remoteStories) && remoteStories.length >= 4) {
                    renderList(remoteStories);
                }
            })
            .catch(() => {
                // 静默保底：使用内置 defaultStories 正常展示
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
