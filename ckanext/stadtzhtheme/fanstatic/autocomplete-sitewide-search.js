"use strict";

ckan.module('autocomplete-sitewide-search', function ($) {
  return {
    initialize: function () {
        new autoComplete({
            selector: 'input#field-sitewide-search[name="q"]',
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
                $.getJSON('/api/3/action/ogdzh_autosuggest', params)
                .done(function(data){
                    response(data.result);
                });
            }
        });
    }
  };
});
