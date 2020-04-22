"use strict";

ckan.module('autocomplete-ogdzh-facet-search', function ($) {
  return {
    initialize: function () {
        new autoComplete({
            selector: 'input#ogdzh_search[name="q"]',
            minChars: 2,
            renderItem: function (item, search){
                // put some searches in quotes, so that solr does not interpret special characters
                var pattern = /\s/;
                if (search.match(pattern)) {
                    item = '"' + item + '"';
                }
                return '<div class="autocomplete-suggestion" data-val="' + item.replace(/"/g, '&quot;') + '">' + item + '</div>';
            },
            source: function(term, response){
                var url = '/api/3/action/ogdzh_autosuggest';
                var params = {q: term};
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
                $.getJSON('/api/3/action/ogdzh_autosuggest', params)
                .done(function(data){
                    response(data.result);
                });
            }
        });
    }
  };
});
