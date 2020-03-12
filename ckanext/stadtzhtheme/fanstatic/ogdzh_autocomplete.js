// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
// ----------------------------------------------------------------------------
// js module ogdzh_autocomplete
// ----------------------------------------------------------------------------
// This js module implements autocompletion for the dataset forms
// - it uses jquery ui autocompletion
// - it uses getJSON to get the data from the ckan api
// - it relies on the action ogdzh_autosuggest
// - it serves 2 forms that are on the same page:
//   therefore there are two id selectors that are served
// - the main search form on the dataset page may have context (e.g. selected
//   facets) that is extracted and added as parameter to the api call

"use strict";

ckan.module('ogdzh_autocomplete', function ($) {
  return {
    initialize: function () {
        var getData = function (request, response) {
            var url = '/api/3/action/ogdzh_autosuggest';
            // search term
            var params = {q: request.term};
            // determine which form is in focus
            var searchForm = $(':focus')[0].id;
            if (searchForm === 'ogdzh_search') {
                // only for the main dataset form:
                // check if any filters/facets are set and send them along
                var values = [];
                $("#dataset-search-form input[name='groups']").each(function (elem) {
                    values.push($(this).val());
                });
                $("#dataset-search-form input[name='license_id']").each(function (elem) {
                    values.push($(this).val());
                });
                $("#dataset-search-form input[name='res_format']").each(function (elem) {
                    values.push($(this).val());
                });
                $("#dataset-search-form input[name='tags']").each(function (elem) {
                    values.push($(this).val());
                });
                if (values) {
                    values = values.map(function(v) { return v.replace(/-/gi, ''); });
                    params.cfq = values.join(' AND ');
                }
            }
            $.getJSON(url, params)
            .done(function (data) {
                response(data.result);
            });
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
