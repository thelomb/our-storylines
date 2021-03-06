// masonry instance and infinite scroll setup
// $(function() {
  var $grid = $('.grid').masonry({
    // options
    itemSelector: '.grid-item',
    columnWidth: 400
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
// });

/*!
 * =======================================================
 *  SIMPLEST TAGS INPUT BEAUTIFIER 2.2.1
 * =======================================================
 *
 *   Author: Taufik Nurrohman
 *   URL: https://github.com/tovic
 *   License: MIT
 *
 * -- USAGE: ---------------------------------------------
 *
 *   var tags = new TIB(document.querySelector('input'));
 *
 * -------------------------------------------------------
 *
 */
!function(e,n,t){function E(e){return n.createElement(e)}function F(e){return Object.keys(e)}function B(e){return F(e).length}var r="__instance__",i=setTimeout,a="innerHTML",o="textContent",u="class",c=u+"Name",f=u+"es",s="toLowerCase",l="replace",d="pattern",m="placeholder",p="indexOf",v="firstChild",y="parentNode",u="Sibling",h="next"+u,g="previous"+u,w="appendChild",N="insertBefore",T="removeChild",u="Attribute",D="set"+u,b="get"+u,M="preventDefault",I="addEventListener";!function(e){e.version="2.2.1",e[r]={},e.each=function(n,t){return i(function(){var i,t=e[r];for(i in t)n(t[i],i,t)},0===t?0:t||1),e}}(e[t]=function(n,u){function O(){H.focus()}function W(e){var t,n=e?this:H;i(function(){t=n[o].split(j.join);for(_ in t)k.set(t[_])},1)}function Y(){H[a]="",H[h][a]=x}var A,H,_,J,k=this,q=Date.now(),x=n[b]("data-"+m)||n[m]||"",j={join:", ",max:9999,escape:[","],alert:!0,text:["Delete “%s%”","Duplicate “%s%”","Please match the requested format: %s%"],classes:["tags","tag","tags-input","tags-output","tags-view"],update:function(){}},L=E("span"),S=E("span"),C="data-tag";e[t][r][n.id||n.name||B(e[t][r])]=k,u="string"==typeof u?{join:u}:u||{};for(_ in j)"undefined"!=typeof u[_]&&(j[_]=u[_]);A=j[d]||n[b]("data-"+d),j[m]&&(x=j[m]),n[c]=j[f][3],L[c]=j[f][0]+" "+j[f][0]+"-"+q,L[I]("click",O,!1),n[I]("focus",O,!1),L.id=j[f][0]+":"+(n.id||q),L[a]='<span class="'+j[f][4]+'"></span>',S[c]=j[f][2],S[a]='<span contenteditable spellcheck="false" style="white-space:nowrap;outline:none;"></span><span>'+x+"</span>",n[y][N](L,n[h]||null),L[v][w](S),H=S[v],k.tags={},k.success=1,k.error=0,k.filter=function(e){return A?!e||new RegExp(A).test(e)?e:!1:(e+"")[l](new RegExp("["+j.join[l](/\s/g,"")+"]|[-\\s]{2,}|^\\s+|\\s+$","g"),"")[s]()},k.update=function(e,t){for(n.value="";(_=L[v][v])&&_[b](C);)L[v][T](_);if(0===e)e=F(k.tags);else{for(_ in e)J=k.filter(e[_]),J&&(k.tags[J]=1);e=F(k.tags)}k.tags={};for(_ in e)k.set(e[_],t);return j.update(k),k},k.reset=function(e){return e=k.filter(e||""),e?delete k.tags[e]:k.tags={},k.update(0,1)},k.set=function(e,t){var a,r=j.alert,i=j.text;if(e=k.filter(e),e===!1)return Y(),r&&(k.error=1,a=(i[2]||e)[l](/%s%/g,A),"function"==typeof r?r(a,e,k):alert(a)),k;if(""===e||B(k.tags)>=j.max)return Y(),k;var o=E("span"),u=E("a");return o[c]=j[f][1],o[D](C,e),u.href="javascript:;",u.title=(i[0]||"")[l](/%s%/g,e),u[I]("click",function(e){var n=this,t=n[y],r=n[y][b](C);t[y][T](t),k.reset(r),O(),e[M]()},!1),o[w](u),Y(),k.tags[e]?t?L[v][N](o,S):r&&(k.error=1,a=(i[1]||e)[l](/%s%/g,e),"function"==typeof r?r(a,e,k):alert(a)):(k.tags[e]=1,L[v][N](o,S)),n.value=F(k.tags).join(j.join),!t&&j.update(k),k},function(){return H[I]("blur",function(){k.error=0,k.set(this[o])},!1),H[I]("paste",W,!1),H[I]("keydown",function(e){k.error=0;var D,n=this,t=e.keyCode,r=L,u=j.escape,c=(e.key||String.fromCharCode(t))[s](),f=e.ctrlKey,l=e.shiftKey,d=S[g]&&S[g][b](C),m=H[h],v="tab"===c||!l&&9===t,w="enter"===c||!l&&13===t,N=" "===c||!l&&32===t,T="backspace"===c||!l&&8===t;if(!f&&w&&-1===u[p]("\n")){for(;r=r[y];)if("form"===r.nodeName[s]()){D=r;break}k.set(n[o]),0===k.error&&D&&D.submit()}else if(f&&("v"===c||!l&&86===t))W();else if(!n[o]&&T)k.reset(d),O();else{var I,E;for(_ in u)if(I=u[_],E="s"===I,(E||" "===I)&&v||(E||"\n"===I)&&w||(E||" "===I)&&N)return i(function(){k.set(n[o]),O()},1),void e[M]();i(function(){var e=n[o];for(m[a]=e?"":x,_=0,J=u.length;J>_;++_)if(u[_]&&-1!==e[p](u[_])){k.set(e.split(u[_]).join(""));break}},1)}},!1),k}(),k.update(n.value.split(j.join),1),k.config=j,k.input=S,k.view=L,k.target=k.output=n})}(window,document,"TIB");


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

var tag_beautifier_config = {
    join: ', ', // Tags joiner of the output value
    max: 9999, // Maximum tags allowed
    escape: [','], // List of character(s) used to trigger the tag addition
    pattern: false, // Custom pattern to filter the tag name [^1]
    placeholder: false, // Custom tags input placeholder [^2]
    alert: true,
    text: ['Delete \u201C%s%\u201D', 'Duplicate \u201C%s%\u201D', 'Please match the requested format: %s%'],
    classes: ['tags form-control form-control-lg', 'tag', 'tags-input', 'tags-output', 'tags-view'], // HTML classes
    update: function($) {} // Hook that will be triggered on every tags item update
};


//var tags = new TIB(document.querySelector('input[name="tags"]'), tag_beautifier_config);

