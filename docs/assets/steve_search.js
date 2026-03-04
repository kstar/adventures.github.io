// Search function shared between steve.ngc.htm and the generated notes pages
function steveSearchGo(catalogSelectId, objectInputId) {
    var catalog = document.getElementById(catalogSelectId).value;
    var val = document.getElementById(objectInputId).value;
    var number = parseInt(val);
    var maxes = {NGC: 7840, IC: 5386, UGC: 12915};
    if (isNaN(number) || number < 1 || number > maxes[catalog]) {
        alert('Enter a valid ' + catalog + ' number (1\u2013' + maxes[catalog] + ')');
        return;
    }
    var page = Math.floor((number - 1) / 1000);
    var filename;
    if (catalog === 'UGC') {
        filename = catalog + '.html';
    } else {
        filename = catalog + page + '.html';
    }
    window.location.href = '/' + filename + '#' + catalog + '%20' + number;
}
