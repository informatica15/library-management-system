document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Lucide Icons (if loaded from CDN)
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // 2. Mobile menu toggle
    const menuBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.getElementById('sidebar');
    
    if (menuBtn && sidebar) {
        menuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('-translate-x-full');
        });
    }

    // 3. Auto-dismiss flash messages
    const alerts = document.querySelectorAll('.flash-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease-out';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 4000);
    });

    // 4. Quick Close for Alert message
    const alertCloseBtns = document.querySelectorAll('.alert-close-btn');
    alertCloseBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const alertElement = e.target.closest('.flash-alert');
            if (alertElement) {
                alertElement.remove();
            }
        });
    });
});
