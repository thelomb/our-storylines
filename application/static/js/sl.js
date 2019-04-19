// masonry instance and infinite scroll setup
// $(function() {
  var $grid = $('.grid').masonry({
    // options
    itemSelector: '.grid-item',
    columnWidth: '.grid-sizer',
    percentPosition: true
    });

  $grid.imagesLoaded().progress( function() {
    $grid.masonry('layout');
  });

  // get Masonry instance
  var msnry = $grid.data('masonry');

  $grid.infiniteScroll({
    // options
    path: '.pagination__next',
    append: '.grid-item',
    outlayer: msnry,
    status: '.scroller-status',
    hideNav: '.infinite-pagination',
    checkLastPage: true,
  });

$(function () {
    $('#datetimepicker1').datetimepicker({
      format: 'L',
      locale: 'fr',
      viewMode: 'months',

    });
});

$.extend(true, $.fn.datetimepicker.defaults, {
  icons: {
    time: 'fa fa-clock',
    date: 'fa fa-calendar',
    up: 'fa fa-arrow-up',
    down: 'fa fa-arrow-down',
    previous: 'fa fa-chevron-left',
    next: 'fa fa-chevron-right',
    today: 'fa fa-calendar-check',
    clear: 'fa fa-trash-alt',
    close: 'fa fa-times-circle'
  }
});
