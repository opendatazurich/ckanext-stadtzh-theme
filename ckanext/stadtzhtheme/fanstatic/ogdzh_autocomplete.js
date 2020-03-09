// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
// ----------------------------------------------------------------------------
// js module ogdzh_autocomplete
// ----------------------------------------------------------------------------
// This js module implements autocompletion for the dataset forms
// - it uses jquery ui autocompletion
// - it uses getJSON to get the data from the api
// - it relies on the api action ogdzh_autosuggest
// - it serves 2 forms that are on the same page:
//   therefore for 2 id selectors are served

"use strict";

ckan.module('ogdzh_autocomplete', function ($) {
  return {
    initialize: function () {
        var getData = function (request, response) {
            console.log("new search");
            var url = '/api/3/action/ogdzh_autosuggest';
            var params = {q: request.term};
            // check if any filters/facets are set and send them along
            var values = [];
            var filtered = $('.filtered');

            //console.log(filtered);
            for (var i = 0; i < filtered.length; i++) {
                var value = filtered[i].innerText.trim();
                if (value !== "Creative Commons CCZero") {
                    values.push(value);
                }
            }
            params.cfq = values.join(' AND ');
            $.getJSON(url, params)
            .done(function (data) {
                response(data.result);
            });
            console.log(params.cfq);
        };

        // search field on the page

        var selectItem = function (event, ui) {
            $("#ogdzh_search").val(ui.item.value);
            return false;
        };
        $("#ogdzh_search").autocomplete({
            source: getData,
            select: selectItem,
            minLength: 2,
        });

        // search field in the site header
        
        var siteSelectItem = function (event, ui) {
            $("#field-sitewide-search").val(ui.item.value);
            return false;
        };
        $("#field-sitewide-search").autocomplete({
            source: getData,
            select: siteSelectItem,
            minLength: 2,
        });
    }
    };
});