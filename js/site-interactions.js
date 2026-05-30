(function () {
  function ready(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  ready(function () {
    var backToTop = document.getElementById('backToTop');
    if (backToTop) {
      var toggleBackToTop = function () {
        if (window.scrollY > 360) {
          backToTop.classList.add('visible');
        } else {
          backToTop.classList.remove('visible');
        }
      };

      backToTop.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });

      window.addEventListener('scroll', toggleBackToTop, { passive: true });
      toggleBackToTop();
    }

    var tagSearch = document.getElementById('tagSearch');
    if (tagSearch) {
      var tagCards = Array.prototype.slice.call(document.querySelectorAll('.tags-page .tag-cloud li'));
      var tagGroups = Array.prototype.slice.call(document.querySelectorAll('.tags-page .tag-group'));

      tagSearch.addEventListener('input', function () {
        var keyword = tagSearch.value.trim().toLowerCase();

        tagCards.forEach(function (item) {
          var text = item.textContent.toLowerCase();
          item.style.display = !keyword || text.indexOf(keyword) >= 0 ? '' : 'none';
        });

        tagGroups.forEach(function (group) {
          var text = group.textContent.toLowerCase();
          group.style.display = !keyword || text.indexOf(keyword) >= 0 ? '' : 'none';
        });
      });
    }
  });
})();
