#!/usr/bin/env node
/**
 * MCP Server generated from OpenAPI spec for search-v2 v1.0
 * Generated on: 2025-06-25T22:18:54.096Z
 */

// Load environment variables from .env file
import dotenv from 'dotenv';
dotenv.config();

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  type Tool,
  type CallToolResult,
  type CallToolRequest
} from "@modelcontextprotocol/sdk/types.js";
import { setupStreamableHttpServer } from "./streamable-http.js";

import { z, ZodError } from 'zod';
import { jsonSchemaToZod } from 'json-schema-to-zod';
import axios, { type AxiosRequestConfig, type AxiosError } from 'axios';

/**
 * Type definition for JSON objects
 */
type JsonObject = Record<string, any>;

/**
 * Interface for MCP Tool Definition
 */
interface McpToolDefinition {
    name: string;
    description: string;
    inputSchema: any;
    method: string;
    pathTemplate: string;
    executionParameters: { name: string, in: string }[];
    requestBodyContentType?: string;
    securityRequirements: any[];
}

/**
 * Server configuration
 */
export const SERVER_NAME = "search-v2";
export const SERVER_VERSION = "1.0";
export const API_BASE_URL = "https://api.211.org/resources/v2/search";

/**
 * MCP Server instance
 */
const server = new Server(
    { name: SERVER_NAME, version: SERVER_VERSION },
    { capabilities: { tools: {} } }
);

/**
 * Map of tool definitions by name
 */
const toolDefinitionMap: Map<string, McpToolDefinition> = new Map([

  ["get-filters-service-area-values-type-type-dataowners-dataowners", {
    name: "get-filters-service-area-values-type-type-dataowners-dataowners",
    description: `Returns a list of service area values for a given geography type (e.g. county). Type values are: locality, postalCode, county, state, country.

A service area is the geographic area that a service is available. Returned values can be used in the service areas filter on the Search/Keyword API operation (POST method only).

Enter the 'scope' value to filter values to the geographic area type (eg. county). Enter the 'dataOwners' value(s) to filter values on the entered 211 data owner(s) (eg. 211ventura or 211ventura,211northcarolina). 
Refer to the DataOwners filter for a list of 211 data owner(s) that can be used. 

Use the typeFilter and typeFilterValue to filter a dataOwner(s) service area values on one or more higher geographical types. As an example, 211 North Carolina has service areas outside the state of North Carolina assigned to several of its resources. Without a filter, service areas outside 
of North Carolina will be returned. Remove values for service areas outside of North Carolina by setting the 'typeFilter' to 'state' and 'typeFilterValues' to 'North Carolina'. Set multiple values for typeFilterValues by separating values with a comma (e.g. North Carolina,California).

Example: enter 'county' as 'type' and '211ventura' as 'dataOwners' to return a complete list of all service area county values. Use the results to create a search filter that can be added to the search filters 
in the the Search/Keyword API operation (POST method) to filter service at location resources (eg. {"field": "serviceAreas", "value": [{"type": "county","value": "Ventura"},{"type": "county","value": "San Luis Obispo"}]} ).`,
    inputSchema: {"type":"object","properties":{"type":{"type":"string","description":"geography type to filter service area values (eg. locality, postalCode, county, state, country). Multiple type values not supported."},"dataOwners":{"type":"string","description":"211 data owner(s) to filter service area values (e.g. 211ventura OR 211ventura,211northcarolina). See DataOwners API fitler operation for 211 center values."},"typeFilter":{"type":"string","description":"geography type to filter type values (e.g. state). Multiple types not supported."},"typeFilterValues":{"type":"string","description":"value(s) used by type filtergeography type to filter location values (eg. North Carolina OR North Carolina, California). Multiple values supported."}},"required":["type","dataOwners"]},
    method: "get",
    pathTemplate: "/filters/service-area-values",
    executionParameters: [{"name":"type","in":"query"},{"name":"dataOwners","in":"query"},{"name":"typeFilter","in":"query"},{"name":"typeFilterValues","in":"query"}],
    requestBodyContentType: undefined,
    securityRequirements: [{"apiKeyHeader":[]},{"apiKeyQuery":[]}]
  }],
  ["get-filters-location-values-type-type-dataowners-dataowners", {
    name: "get-filters-location-values-type-type-dataowners-dataowners",
    description: `Returns a list of distinct location values for a given geography type (e.g. county). A location is where a service is delivered. Possible values are: locality, postalCode, county, state, country.

Returned values can be used in the locationAddresses parameter on the Search/Keyword API operation (POST method method). 

Example: enter 'county' as 'type' and '211ventura' as 'dataOwners' to return a complete list of all counties assigned to 211ventura locations. Use the typeFilter and typeFilterValue to filter a dataOwner(s) 
location values on one or more higher geographical types. As an example, 211 North Carolina has locations outside the state of North Carolina assigned to several of its resources. Without a filter, locations outside 
of North Carolina will be returned. Remove values for locations outside of North Carolina by setting the 'typeFilter' to 'state' and 'typeFilterValues' to 'NC'. Set multiple values for typeFilterValues by separating values with a comma (e.g. NC,CA).

Use the results to create a search filter for the Search/Keyword API operation (POST method) (eg. {"field": "address/county", "value": [{"type": "county","value": "Ventura"},{"type": "county","value": "San Luis Obispo"}]} ).`,
    inputSchema: {"type":"object","properties":{"type":{"type":"string","description":"geography type to filter location values (eg. locality, postalCode, county, state, country). Multiple types not supported."},"dataOwners":{"type":"string","description":"data owner(s) to filter value (e.g. 211ventura OR 211ventura,211northcarolina). See DataOwners API fitler operation for 211 center values."},"typeFilter":{"type":"string","description":"geography type to filter type values (e.g. state). Multiple types not supported."},"typeFilterValues":{"type":"string","description":"value(s) used by type filtergeography type to filter location values (eg. North Carolina OR North Carolina, California). Multiple values supported."}},"required":["type","dataOwners"]},
    method: "get",
    pathTemplate: "/filters/location-values",
    executionParameters: [{"name":"type","in":"query"},{"name":"dataOwners","in":"query"},{"name":"typeFilter","in":"query"},{"name":"typeFilterValues","in":"query"}],
    requestBodyContentType: undefined,
    securityRequirements: [{"apiKeyHeader":[]},{"apiKeyQuery":[]}]
  }],
  ["get-filters-data-owners", {
    name: "get-filters-data-owners",
    description: `Returns all 211 center data owners and data owners display name values. A 211 data owner is the creator or steward of the resource data. 
Returned values can be used in the 'dataOwners' parameter of the Search/Keyword API operation (GET and POST methods).

Example 1: Use the results to create a search filter that can be added to the search filters in the of the Search/Keyword API operation (POST method) to filter service at location resources (eg. {"field": "dataOwner", "value": ["211ventura","211northcarolina"]} ).

Example 2: Use the results to create a search filter that can be added to the search filters in the of the Search/Keyword API operation (POST method) to filter service at location resources (eg. {"field": "dataOwnerDisplayName", "value": ["211 Ventura","211 North Carolina"]} ).`,
    inputSchema: {"type":"object","properties":{}},
    method: "get",
    pathTemplate: "/filters/data-owners",
    executionParameters: [],
    requestBodyContentType: undefined,
    securityRequirements: [{"apiKeyHeader":[]},{"apiKeyQuery":[]}]
  }],
  ["get-filters-taxonomy-level2-terms", {
    name: "get-filters-taxonomy-level2-terms",
    description: `Returns all level 2 taxonomy term values, grouped by level 1 term. This API operation can be used to create a list of topics and subtopics.

List can be filtered on one or more 211 data owners`,
    inputSchema: {"type":"object","properties":{"dataOwners":{"type":"string","description":"211 data owner(s) to filter values (e.g. 211ventura or 211ventura,211northcarolina). \r\n            See DataOwner API fitler operation for 211 center values. Leave blank if wanting all level 2 terms for all 211s."}}},
    method: "get",
    pathTemplate: "/filters/taxonomy-level2-terms",
    executionParameters: [{"name":"dataOwners","in":"query"}],
    requestBodyContentType: undefined,
    securityRequirements: [{"apiKeyHeader":[]},{"apiKeyQuery":[]}]
  }],
  ["get-filters-taxonomy-terms-by-level-level-level", {
    name: "get-filters-taxonomy-terms-by-level-level-level",
    description: `Returns all taxonomy term values at selected level of the AIRS taxonomy tree structure for the selected 211 center(s). 

As an example, enter '2' as 'level' and '211ventura' as 'dataOwners' to return all Level 2 taxonomy terms assigned to 211ventura resources.`,
    inputSchema: {"type":"object","properties":{"level":{"type":"string","description":"level of taxonomy to filter values. Accepted values are: 1, 2, 3, 4, 5 or 6. Multiple levels not supported."},"dataOwners":{"type":"string","description":"211 data owner(s) to filter values (e.g. 211ventura or 211ventura,211northcarolina). See DataOwners API fitler operation for 211 center values."}},"required":["level"]},
    method: "get",
    pathTemplate: "/filters/taxonomy-terms-by-level",
    executionParameters: [{"name":"level","in":"query"},{"name":"dataOwners","in":"query"}],
    requestBodyContentType: undefined,
    securityRequirements: [{"apiKeyHeader":[]},{"apiKeyQuery":[]}]
  }],
  ["get-filters-taxonomy-terms-assigned-level-level-levelterm-levelterm-dataowne", {
    name: "get-filters-taxonomy-terms-assigned-level-level-levelterm-levelterm-dataowne",
    description: `Returns all child service taxonomy terms assigned to a 211 center(s) resource data for a given parent taxonomy term (eg. 'Food' is a child term to parent term 'Basic Needs'). 
Returned values can be filtered by selected term and level. This API can be used to return values that can be used to find resources indexed at any level below a selected parent.

This API returns values that can be used as 'taxonomyTerm' parameter value inputs on the Search/Keyword API operation. 

As an example, enter '1' as 'level', 'Basic Needs' as 'levelTerm', and '211ventura' as 'dataOwners' to return all taxonomy 
terms (Level2 through Level6 in this example) assigned to 211ventura resources with a Level 1 term of 'Basic Needs' (ie. returns all resources assigned a taxonomy term with parent term equal 
to 'Basic Needs'. 

As another example, enter '2' as 'level' and 'Food' and 'levelTerm', and '211ventura,211northcarolina' as 'dataOwners' to return all taxonomy terms (Level3 through Level6 in this example) 
assigned to 211ventura or 211northcarolina resources with a Level 2 term of 'Food' (ie. returns all resources assigned a taxonomy term with parent Level 2 term equal to 'Food'.  To return all terms assigned, 
regardless of level, enter '*' for 'level' and 'levelTerm'.`,
    inputSchema: {"type":"object","properties":{"level":{"type":"string","description":"level of taxonomy terms to filter values. Accepted values are: 1, 2, 3, 4, 5 or 6. Multiple levels not supported."},"levelTerm":{"type":"string","description":"level term to filter values, in combination with the entered level (eg. Basic Needs). See Taxonomy Terms by Level API operation for possible level term values. Multiple terms not supported."},"dataOwners":{"type":"string","description":"211 data owner(s) to filter values (e.g. 211ventura or 211ventura,211northcarolina). See DataOwners API fitler operation for 211 center values."}},"required":["level","levelTerm","dataOwners"]},
    method: "get",
    pathTemplate: "/filters/taxonomy-terms-assigned",
    executionParameters: [{"name":"level","in":"query"},{"name":"levelTerm","in":"query"},{"name":"dataOwners","in":"query"}],
    requestBodyContentType: undefined,
    securityRequirements: [{"apiKeyHeader":[]},{"apiKeyQuery":[]}]
  }],
  ["get-filters-taxonomy-terms-and-codes-assigned-level-level-levelterm-levelter", {
    name: "get-filters-taxonomy-terms-and-codes-assigned-level-level-levelterm-levelter",
    description: `Returns all service taxonomy terms and codes assigned to a 211 center(s) resource data. Returned values can be filtered by selected term and level.

As an example, enter '1' as 'level', 'Basic Needs' as 'levelTerm', and '211ventura' as 'dataOwners' to return all taxonomy 
terms (Level2 through Level6 in this example) assigned to 211ventura resources with a Level 1 term of 'Basic Needs' 
(ie. returns all resources assigned a taxonomy term with parent term equal to 'Basic Needs'.

As another example, enter '2' as 'level' and 'Food' and 'levelTerm', and '211ventura,211northcarolina' as 'dataOwners' to return all taxonomy 
terms (Level3 through Level6 in this example) assigned to 211ventura or 211northcarolina resources with a Level 2 term of 'Food' (ie. returns all resources assigned a 
taxonomy term with parent Level 2 term equal to 'Food'.

To return all terms assigned, regardless of level, enter '*' for 'level' and 'levelTerm'. Note: to return only terms, see Taxonomy Term Values Assigned API operation.`,
    inputSchema: {"type":"object","properties":{"level":{"type":"string","description":"taxonomy term level to filter values. Accepted values are: 1, 2, 3, 4, 5 or 6. Multiple levels not supported."},"levelTerm":{"type":"string","description":"filters assigned taxonomy terms by term, in combination with the entered level (eg. Basic Needs). See Taxonomy Terms by Level API operation for possible level term values. Multiple terms not supported."},"dataOwners":{"type":"string","description":"211 data owner(s) to filter values(e.g. 211ventura or 211ventura,211northcarolina). See DataOwners API fitler operation for 211 center values."}},"required":["level","levelTerm","dataOwners"]},
    method: "get",
    pathTemplate: "/filters/taxonomy-terms-and-codes-assigned",
    executionParameters: [{"name":"level","in":"query"},{"name":"levelTerm","in":"query"},{"name":"dataOwners","in":"query"}],
    requestBodyContentType: undefined,
    securityRequirements: [{"apiKeyHeader":[]},{"apiKeyQuery":[]}]
  }],
  ["get-filters-tags-dataowners-dataowners", {
    name: "get-filters-tags-dataowners-dataowners",
    description: `Returns all tags for selected 211 data owner(s).

This API provides the caller with values that can be used in the tags parameter of the Search/Keywords API operation.`,
    inputSchema: {"type":"object","properties":{"dataOwners":{"type":"string","description":"211 data owner(s) to filter values (e.g. 211ventura or 211ventura,211northcarolina).  See DataOwners API fitler operation for 211 center values."}},"required":["dataOwners"]},
    method: "get",
    pathTemplate: "/filters/tags",
    executionParameters: [{"name":"dataOwners","in":"query"}],
    requestBodyContentType: undefined,
    securityRequirements: [{"apiKeyHeader":[]},{"apiKeyQuery":[]}]
  }],
  ["get-keyword-keywords-keywords-location-location", {
    name: "get-keyword-keywords-keywords-location-location",
    description: `Searches an index of NDP service at location records. 

Records are returned in 'service-at-location' format, with all services and locations of the organization. For more options, use the POST method. 

The total number of records in the index matching the request is identified as "count" at the top of the response. The values set for each parameter are also returned within the request object at the top of the response, when 'resultsAdvanced' is set to 'true'.

Filter expressions can be applied to the GET and POST operations using parameters such as data owners, tags, taxonomy codes, service areas, and address. See parameter value descriptions for more information.

Note: A search that returns no results will have a status code of 204 or 404. A 204 status code is returned when the Advanced Results parameter value is 
is to false. When set to true, a 404 NotFound status code is returned with the request input. Note that the request input may be programitically modified in certain scenarios. As an example, 
when 'searchWithinLocationType' is set to its default value 'unknown', the geocoding service will set the location type based on the location entered. Refer to the field description for more information. 
A 500 ServerError response returns a tracking code that can be used internally to identify undocumented items and/or resolve unmanaged errors.`,
    inputSchema: {"type":"object","properties":{"keywords":{"type":"string","description":"One or more keywords to search the repository. Set SearchMode to 'Any' to match on at least one keyword. \r\n           Set SearchMode to 'All' to match on all words. To search on taxonomy term(s), set KeywordIsTaxonomyTerm to true. To search on taxonomy code(s), \r\n           set KeywordIsTaxonomyCode to true. More detail on taxonomy searches: For taxonomy code or taxonomy term searches, set SearchMode to 'All' to require all taxonomy terms be assigned \r\n           to resources returned with search results. Set SearchMode to 'Any' to require a match on at least one taxonomy term/code. Wildcards can be used to \r\n           search resources with a partial taxonomy code (eg. BD\\*). All resources with taxonomy codes matching the characters before * will be returned. \r\n           As an example, a taxonomy code search for BD* will return all resources with a taxonomy code beginning with BD, the taxonomy code for Food. \r\n           Using taxonomy code wildcard searches ensures all resources with 'child' taxonomy codes are returned (eg. BD-1800 is a child of BD, and would be \r\n           returned with the BD* wildcard taxonomy code search). Wilcards can also be used for taxonomy term searches, and will return matches on all taxonomy terms matching on one or more terms located within the full taxonmy term\r\n           (eg. Food Pantry can be match on Food and/or Pantry). A match occurs when all characters before the \\* are matched on or more terms with the full taxonomy term. As as example, a wilcard search on Food* will return \r\n           resources with taxonomy term(s) that include any word within its taxonomy term(s) beginning with 'Food'. A search for F\\* will return resources with taxonomy term(s) beginning with F)."},"location":{"type":"string","description":"Location to search for resources. Value can be a zip code, city, county, state, country or \r\n           longitude_latitude pair. (note regading longitude_latitude location values: longitude_latitude locations must follow this format lon:-119.293106_lat:34.28083 and can include up to a maximum of six digits after the decimal). \r\n           There are four patterns for location searching: near, within, serving, servingOnly. The pattern is contolled by LocationMode. See LocationMode for details on using each pattern."},"distance":{"type":"number","format":"int32","description":"Format - int32. Maximum distance from the entered location to the physical address where the resource is availalble (ie. service is delivered). \r\n           Set 'OrderByDistance' to true to sort search results from nearest to farthest from enetered location. Distance is ignored (set by the system to 0) \r\n           when LocationMode is set to 'Within' because distance is not applicable when searching within a geographic boundary. Distance is set to 5000, when \r\n           LocationMode set to 'Serving' or 'ServingOnly' to ensure all resources with assigned with the selected service areas area returned \r\n           (ie. locations are considered service areas when LocationMode set to 'Serving' or 'ServingOnly'). As an example, a service (ie. resource) may be \r\n           physically located in California but have service areas throughout the country (eg. helplines)."},"dataOwners":{"type":"string","description":"Comma-delimited list of data owners to filter search results. Adding one or more values will programatically add a search filter. If multiple data owners are applied (eg. 211ventura,211bayarea), a match on one or more data owners will result in a match (and resource returned). The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' (eg. ne,and||211ventura,211ayarea). See /filters/dataOwners on Filters API for a list of data owners."},"tagsService":{"type":"string","description":"Comma-delimited list of tags to filter search results. Adding one or more values will programatically add a search filter. The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' (eg. ne,and||211ventura,211ayarea). If multiple tags are applied (eg. Kinship,Shelter), a match on one or more tags will result in a match (and resource returned). To match on all tags, set Assert operator value to 'eq' and Join operator value to 'and'. See /filters/tags on Filters API for a list of tags."},"searchWithinLocationType":{"enum":["Unknown","City","County","PostalCode","State","Country"],"type":"string","description":"Type of the location used to set the geographic boundary for searching for resources when LocationMode set to 'Within'. \r\n           Values are City, County, PostalCode, State, Country, Unknown. As an example, if SearchWithinLocationType is set to 'City' with location set to 'Ventura', \r\n           resources with a physical location within the geographic boundary of the city of Ventura will be returned. if SearchWithinLocationType is set to 'County' \r\n           with location set to 'Ventura', resources with a physical location within the geographic boundary of the county of Ventura will be returned. Default value \r\n           is 'Unknown'. If value is set to 'Unknown' (or not set), the LocationType will be determined using the service."},"skip":{"type":"number","format":"int32","default":0,"description":"Format - int32. Number of results to skip. Used with Size to page results. Note that the total number of resources that match the search is returned with 'count' in the search results, \r\n           if IncludeTotalCount is set to true."},"size":{"type":"number","format":"int32","default":10,"description":"Format - int32. Number of results to be returned. Used with Skip to page results. Note that the total number of resources that match the search is returned with 'count' in the search results, \r\n           if IncludeTotalCount is set to true."},"searchMode":{"enum":["All","Any"],"type":"string","description":"Set to 'Any' to match one or more entered search keywords in simple text search. Set to 'All' to match on all search keywords. Default is 'All'."},"locationMode":{"enum":["Within","Near","Serving","ServingOnly"],"type":"string","description":"To search for resources 'near' the location, set LocationMode to 'Near', and 'Distance' to a value greater than 0. \r\n           This will return resources with service delivery locations within the chosen distance from the geographic center (latitude/longitude) of the chosen location. \r\n           To search for resources 'within' the geographic boundary of the location, set LocationMode to 'Within'. This will return resources within the boundary \r\n           (polygon of latitude/longitude values) of the chosen location. To search for resources avaialable within a service area (a geographic area that often defines \r\n           eligibility for service), set LocationMode to 'Serving' or 'ServingOnly'. ServingOnly returns resources available within the chosen location (ie. chosen service area). \r\n           Serving returns resources delivered within the chosen location, plus all higher level service area boundaries. As an example, setting LocationMode 'ServingOnly' \r\n           and location to 'Ventura' will return all resources with a service area of Ventura. If LocationMode is set to 'Serving', resources with a service area of \r\n           California and United States will also be returned, as Ventura is a service areas within the higher level service areas of California (state) and United States (country). \r\n           Notes: Distance is ignored when LocationMode is set to 'Within', 'Serving' and 'ServingOnly'. OrderByDistance is ignored when LocationMode is set to 'Within'."},"keywordIsTaxonomyCode":{"type":"boolean","default":false,"description":"Set to false for regular text search. Set to true to search on taxonomy code or taxonomy code with wild card (e.g. BD-1800 or BD-1800*). Wildcard codes return code and any-child codes. Separate multiple codes with comma (eg. BD-1800,LM-200*). See /filters/taxonomy-terms-and-codes-assigned Filters API for a list of codes."},"keywordIsTaxonomyTerm":{"type":"boolean","default":false,"description":"Set to false for regular text search. Set to 'true' if keyword is a taxonomy term or taxonomy terms (eg. Food Pantry). Separate multiple terms with comma (Food Pantry,Emergency Shelter). Wildcards cannot be used with terms. See /filters/taxonomy-terms-assigned Filters API for a list of terms."},"resultsAdvanced":{"type":"boolean","default":false,"description":"Set to 'true' to return all search request and result details, including the geocoded location and the request input data (which may have been programatically modified). Note: this can help users understand restrictions to search requests implemented through policy, including changes applied to parameter and header arguments."},"orderByDistance":{"type":"boolean","default":true,"description":"Set to true to order results from nearest to farthest from entered location. (note: orderByDistance applies only to locationMode 'Near' searches only.)"},"taxonomyTerms":{"type":"string","description":"Comma-delimited list of taxonomy terms to filter data on. Adding one or more values will programatically add a search filter. Multiple terms can be added, and wildcards are supported (eg. Food\\*,Food Pantry ). Create a wildcard by appending * to the end of the term, returning all children. The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' (eg. ne,and||Food*,Food Pantry). If multiple terms are applied (eg. Food Pantry,Medical*), a match on one or more terms will result in a match (and resource returned). To match on all terms, set Assert operator value to 'eq' and Join operator value to 'and'. See /filters/taxonomy-terms-assigned Filters API for a list of terms."},"taxonomyCodes":{"type":"string","description":"Comma-delimited list of taxonomy codes to filter data on. Adding one or more values will programatically add a search filter. Multiple codes can be added, and wildcards are supported (eg. BD-1800\\*,PX-2300,HD-8000.1800* ). Create a wildcard by appending * to the end of the code, returning all children. The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' (eg. ne,and||Older Adults,Women). If multiple terms are applied (eg. Older Adults,Women), a match on one or more terms will result in a match (and resource returned). To match on all terms, set Assert operator value to 'eq' and Join operator value to 'and'. See /filters/taxonomy-terms-and-codes-assigned Filters API for a list of terms."},"targetTerms":{"type":"string","description":"Comma-delimited list of target terms to filter data on. A target term is a Y-level AIRS taxonomy term. Adding one or more values will programatically add a search filter. The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' (eg. ne,and||Older Adults,Women). If multiple terms are applied (eg. Older Adults,Women), a match on one or more terms will result in a match (and resource returned). To match on all terms, set Assert operator value to 'eq' and Join operator value to 'and'. See /filters/target-terms-assigned Filters API for a list of terms."},"serviceAreaCountries":{"type":"string","description":"Comma-delimited list of countries (non-abbreviated format) to filter results on service area (eg. United States,Canada). The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||United States,Canada). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||United States,Canada. (note: operator values joining multiple service area types is set by default to 'or' Join operator and null Assert operator. Multiple service area type operator values can only be set in POST operation. See /filters/service-area-values on Filters API for a list of service areas."},"serviceAreaStates":{"type":"string","description":"Comma-delimited list of states (non-abbreviated format) to filter results on service area (eg. North Carolina,California).  The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||North Carolina,California). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||North Carolina,California). (note: operator values joining multiple service area types is set by default to 'or' Join operator and null Assert operator. Multiple service area type operator values can only be set in POST operation. See /filters/service-area-values on Filters API for a list of service areas."},"serviceAreaCounties":{"type":"string","description":"Comma-delimited list of counties to filter results on service area (eg. Wake,Durham).  The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||Wake,Durham). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||Wake,Durham). (note: operator values joining multiple service area types is set by default to 'or' Join operator and null Assert operator. Multiple service area type operator values can only be set in POST operation. See /filters/service-area-values on Filters API for a list of service areas."},"serviceAreaCities":{"type":"string","description":"Comma-delimited list of cities to filter results on service area (eg. Raleigh,San Francisco).  The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||Raleigh,San Francisco). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||Raleigh,San Francisco). (note: operator values joining multiple service area types is set by default to 'or' Join operator and null Assert operator. Multiple service area type operator values can only be set in POST operation. See /filters/service-area-values on Filters API for a list of service areas."},"serviceAreaPostalCodes":{"type":"string","description":"Comma-delimited list of postal codes to filter results on service area (eg. 95945,95350).  The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||95945,95350). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||95945,95350). (note: operator values joining multiple service area types is set by default to 'or' Join operator and null Assert operator. Multiple service area type operator values can only be set in POST operation. See /filters/service-area-values on Filters API for a list of service areas."},"addressCountries":{"type":"string","description":"Comma-delimited list of countries (non-abbreviated format) to filter results on location address (eg. United States,Canada). The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||United States,Canada). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||United States,Canada). (note: operator values joining multiple address types is set by default to 'and' Join operator and null Assert operator. Multiple address type operator values can only be set in POST operation. See /filters/location-values on Filters API for a list of address locations."},"addressStates":{"type":"string","description":"Comma-delimited list of states (abbreviated format) to filter results on location address (eg. NC,CA). The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||NC,CA). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||NC,CA). (note: operator values joining multiple address types is set by default to 'and' Join operator and null Assert operator. Multiple address type operator values can only be set in POST operation. See /filters/location-values on Filters API for a list of address locations."},"addressCounties":{"type":"string","description":"Comma-delimited list of counties to filter results on location address (eg. Wake,Durham). The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||Wake,Durham). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||Wake,Durham). (note: operator values joining multiple address types is set by default to 'and' Join operator and null Assert operator. Multiple address type operator values can only be set in POST operation. See /filters/location-values on Filters API for a list of address locations."},"addressCities":{"type":"string","description":"Comma-delimited list of cities to filter results on location address (eg. Raleigh,San Francisco). The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||Raleigh,San Francisco). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||Raleigh,San Francisco). (note: operator values joining multiple address types is set by default to 'and' Join operator and null Assert operator. Multiple address type operator values can only be set in POST operation. See /filters/location-values on Filters API for a list of address locations."},"addressPostalCodes":{"type":"string","description":"Comma-delimited list of postal codes to filter results on location address (eg. 95945,95350). The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||95945,95350). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||95945,95350). (note: operator values joining multiple address types is set by default to 'and' Join operator and null Assert operator. Multiple address type operator values can only be set in POST operation. See /filters/location-values on Filters API for a list of address locations."},"ids":{"type":"string","description":"Comma-delimited list of unique identifiers (ids) for organization, service, location or service-at-location. Adding one or more values will programatically add a search filter. Only default operator values 'eq' (assert) and 'or' (join) are accepted for this parameter, and are automatically added."}},"required":["keywords","location","locationMode"]},
    method: "get",
    pathTemplate: "/keyword",
    executionParameters: [{"name":"keywords","in":"query"},{"name":"location","in":"query"},{"name":"distance","in":"header"},{"name":"dataOwners","in":"header"},{"name":"tagsService","in":"header"},{"name":"searchWithinLocationType","in":"header"},{"name":"skip","in":"header"},{"name":"size","in":"header"},{"name":"searchMode","in":"header"},{"name":"locationMode","in":"header"},{"name":"keywordIsTaxonomyCode","in":"header"},{"name":"keywordIsTaxonomyTerm","in":"header"},{"name":"resultsAdvanced","in":"header"},{"name":"orderByDistance","in":"header"},{"name":"taxonomyTerms","in":"header"},{"name":"taxonomyCodes","in":"header"},{"name":"targetTerms","in":"header"},{"name":"serviceAreaCountries","in":"header"},{"name":"serviceAreaStates","in":"header"},{"name":"serviceAreaCounties","in":"header"},{"name":"serviceAreaCities","in":"header"},{"name":"serviceAreaPostalCodes","in":"header"},{"name":"addressCountries","in":"header"},{"name":"addressStates","in":"header"},{"name":"addressCounties","in":"header"},{"name":"addressCities","in":"header"},{"name":"addressPostalCodes","in":"header"},{"name":"ids","in":"header"}],
    requestBodyContentType: undefined,
    securityRequirements: [{"apiKeyHeader":[]},{"apiKeyQuery":[]}]
  }],
  ["post-keyword", {
    name: "post-keyword",
    description: `Searches an index of NDP service at location records. 

Records are returned in 'service-at-locationn' format, with all services and locations of the organization.

The total number of records in the index matching the request is identified as "count" at the top of the response. The values set for each parameter are also returned within the request object at the top of the response, when 'resultsAdvanced' is set to 'true'.

Note: Active and Inactive organizations can be returned. Set the 'includeInactive' filter to true to return both active and inactive records. Default value is set to 'false', returning only active records. 

Note: A search that returns no results will have a status code of 204 or 404. A 204 status code is returned when the Advanced Results parameter value is 
is to false. When set to true, a 404 NotFound status code is returned with the request input. Note that the request input may be programitically modified in certain scenarios. As an example, 
when 'searchWithinLocationType' is set to its default value 'unknown', the geocoding service will set the location type based on the location entered. Refer to the field description for more information. 
A 500 ServerError response returns a tracking code that can be used internally to identify undocumented items and/or resolve unmanaged errors.`,
    inputSchema: {"type":"object","properties":{"dataOwners":{"type":"string","description":"(admin use only) Comma-delimited list of data owners to filter search results. Adding one or more values will programatically add a search filter. If multiple data owners are applied (eg. 211ventura,211bayarea), a match on one or more data owners will result in a match (and resource returned). The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' (eg. ne,and||211ventura,211ayarea). See /filters/dataOwners on Filters API for a list of data owners."},"taxonomyCodes":{"type":"string","description":"(admin use only) Comma-delimited list of taxonomy codes to filter data on. Adding one or more values will programatically add a search filter. Multiple codes can be added, and wildcards are supported (eg. BD-1800\\*,PX-2300,HD-8000.1800* ). Create a wildcard by appending * to the end of the code, returning all children. The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' (eg. ne,and||Older Adults,Women). If multiple terms are applied (eg. Older Adults,Women), a match on one or more terms will result in a match (and resource returned). To match on all terms, set Assert operator value to 'eq' and Join operator value to 'and'. See /filters/taxonomy-terms-and-codes-assigned Filters API for a list of terms."},"taxonomyTerms":{"type":"string","description":"(admin use only) Comma-delimited list of taxonomy terms to filter data on. Adding one or more values will programatically add a search filter. Multiple terms can be added, and wildcards are supported (eg. Food\\*,Food Pantry ). Create a wildcard by appending * to the end of the term, returning all children. The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' (eg. ne,and||Food*,Food Pantry). If multiple terms are applied (eg. Food Pantry,Medical*), a match on one or more terms will result in a match (and resource returned). To match on all terms, set Assert operator value to 'eq' and Join operator value to 'and'. See /filters/taxonomy-terms-assigned Filters API for a list of terms."},"targetTerms":{"type":"string","description":"(admin use only) Comma-delimited list of target terms to filter data on. A target term is a Y-level AIRS taxonomy term. Adding one or more values will programatically add a search filter. The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' (eg. ne,and||Older Adults,Women). If multiple terms are applied (eg. Older Adults,Women), a match on one or more terms will result in a match (and resource returned). To match on all terms, set Assert operator value to 'eq' and Join operator value to 'and'. See /filters/target-terms-assigned Filters API for a list of terms."},"tagsService":{"type":"string","description":"(admin use only) Comma-delimited list of tags to filter search results. Adding one or more values will programatically add a search filter. The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' (eg. ne,and||211ventura,211ayarea). If multiple tags are applied (eg. Kinship,Shelter), a match on one or more tags will result in a match (and resource returned). To match on all tags, set Assert operator value to 'eq' and Join operator value to 'and'. See /filters/tags on Filters API for a list of tags."},"skip":{"type":"number","format":"int32","description":"Format - int32. (admin use only) Number of results to skip. Used with Size to page results. Note that the total number of resources that match the search is returned with 'count' in the search results, if IncludeTotalCount is set to true."},"size":{"type":"number","format":"int32","description":"Format - int32. (admin use only) Number of results to be returned. Used with Skip to page results. Note that the total number of resources that match the search is returned with 'count' in the search results, if IncludeTotalCount is set to true."},"serviceAreaCountries":{"type":"string","description":"(admin use only) Comma-delimited list of countries (non-abbreviated format) to filter results on service area (eg. United States,Canada). The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||United States,Canada). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||United States,Canada. (note: operator values joining multiple service area types is set by default to 'or' Join operator and null Assert operator. Multiple service area type operator values can only be set in POST operation. See /filters/service-area-values on Filters API for a list of service areas."},"serviceAreaStates":{"type":"string","description":"(admin use only) Comma-delimited list of states (non-abbreviated format) to filter results on service area (eg. North Carolina,California).  The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||United States,Canada). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||United States,Canada. (note: operator values joining multiple service area types is set by default to 'or' Join operator and null Assert operator. Multiple service area type operator values can only be set in POST operation. See /filters/service-area-values on Filters API for a list of service areas."},"serviceAreaCounties":{"type":"string","description":"(admin use only) Comma-delimited list of counties to filter results on service area (eg. Wake,Durham).  The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||United States,Canada). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||United States,Canada. (note: operator values joining multiple service area types is set by default to 'or' Join operator and null Assert operator. Multiple service area type operator values can only be set in POST operation. See /filters/service-area-values on Filters API for a list of service areas."},"serviceAreaCities":{"type":"string","description":"(admin use only) Comma-delimited list of cities to filter results on service area (eg. Raleigh,San Francisco).  The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||United States,Canada). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||United States,Canada. (note: operator values joining multiple service area types is set by default to 'or' Join operator and null Assert operator. Multiple service area type operator values can only be set in POST operation. See /filters/service-area-values on Filters API for a list of service areas."},"serviceAreaPostalCodes":{"type":"string","description":"(admin use only) Comma-delimited list of postal codes to filter results on service area (eg. 12345,67890).  The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||United States,Canada). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||United States,Canada. (note: operator values joining multiple service area types is set by default to 'or' Join operator and null Assert operator. Multiple service area type operator values can only be set in POST operation. See /filters/service-area-values on Filters API for a list of service areas."},"addressCountries":{"type":"string","description":"(admin use only) Comma-delimited list of countries (non-abbreviated format) to filter results on location address (eg. United States,Canada). The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||United States,Canada). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||United States,Canada). (note: operator values joining multiple address types is set by default to 'and' Join operator and null Assert operator. Multiple address type operator values can only be set in POST operation. See /filters/location-values on Filters API for a list of address locations."},"addressStates":{"type":"string","description":"(admin use only) Comma-delimited list of states (abbreviated format) to filter results on location address (eg. NC,CA). The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||NC,CA). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||NC,CA). (note: operator values joining multiple address types is set by default to 'and' Join operator and null Assert operator. Multiple address type operator values can only be set in POST operation. See /filters/location-values on Filters API for a list of address locations."},"addressCounties":{"type":"string","description":"(admin use only) Comma-delimited list of counties to filter results on location address (eg. Wake,Durham). The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||Wake,Durham). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||Wake,Durham). (note: operator values joining multiple address types is set by default to 'and' Join operator and null Assert operator. Multiple address type operator values can only be set in POST operation. See /filters/location-values on Filters API for a list of address locations."},"addressCities":{"type":"string","description":"(admin use only) Comma-delimited list of cities to filter results on location address (eg. Raleigh,San Francisco). The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||Raleigh,San Francisco). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||Raleigh,San Francisco). (note: operator values joining multiple address types is set by default to 'and' Join operator and null Assert operator. Multiple address type operator values can only be set in POST operation. See /filters/location-values on Filters API for a list of address locations."},"addressPostalCodes":{"type":"string","description":"(admin use only) Comma-delimited list of postal codes to filter results on location address (eg. 12345,67890). The 'eq' Assert operator and the 'or' Join operator are the default operator values. Assert operator value 'ne' can only be used with Join operator 'and' or null (eg. ne,and||12345,67890). Assert operator value 'eq' or null can only be used with Join operator 'or' (eg. eq,or||12345,67890). (note: operator values joining multiple address types is set by default to 'and' Join operator and null Assert operator. Multiple address type operator values can only be set in POST operation. See /filters/location-values on Filters API for a list of address locations."},"ids":{"type":"string","description":"(admin use only) Comma-delimited list of unique identifiers (ids) for organization, service, location or service-at-location. Adding one or more values will programatically add a search filter. Default operator values: Assert = 'eq'; Join='or'. Only default operator values permitted (ie. Assert=eq;Join=or)."},"requestBody":{"required":["location","locationMode","search","size","skip"],"type":"object","properties":{"search":{"minLength":1,"type":"string","description":"One or more keywords to search the repository. Set SearchMode to 'Any' to match on at least one keyword. \r\nSet SearchMode to 'All' to match on all words. To search on taxonomy term(s), set KeywordIsTaxonomyTerm to true.\r\nTo search on taxonomy code(s), set KeywordIsTaxonomyCode to true. For taxonomy code or taxonomy term searches, set SearchMode to 'All'\r\nto require all taxonomy terms be assigned to resources returned with search results. Set SearchMode to 'Any' to require a match on at least\r\none taxonomy term/code. Wildcards can be used to search resources with a partial taxonomy code (eg. BD*) or partial taxonomy term (eg. Emer*). All resources matching the characters \r\nbefore * will be returned. As an example, a taxonomy code search for BD\\* will return all resources with a taxonomy code beginning with BD, the taxonomy\r\ncode for Food. Using taxonomy code wildcard searches ensures all resources with 'child' taxonomy codes are returned (eg. BD-1800 is a child of BD, and would be returned\r\nwith the BD\\* wildcard taxonomy code search). Wilcards can also be used for taxonomy term searches, and will return matches on all taxonomy terms matching on one or more terms located within the full taxonmy term\r\n(eg. Food Pantry can be match on Food and/or Pantry). A match occurs when all characters before the \\* are matched on or more terms with the full taxonomy term. As as example, a wilcard search on Food* will return \r\nresources with taxonomy term(s) that include any word within its taxonomy term(s) beginning with 'Food'. A search for F\\* will return resources with taxonomy term(s) beginning with F)."},"location":{"minLength":1,"type":"string","description":"Location to search for resources.Value can be a zip code, city, county, state, country or longitude_latitude pair. There are four patterns for location searching: \r\nnear, within, serving, servingOnly. The pattern is contolled by LocationMode. See LocationMode for details on using each pattern. (Notes ==> note 1: latidude and longitude: when using latitude and longitude for location: \r\nlongitude_latitude values must be provided as lon:-119.293106_lat:34.28083 and can include up to a maximum of six digits after the decimal. note 2: the search API geocodes locations and may use the geocoded data\r\nwithin the search logic. to view the geocoded data of the entered location, set the parameter 'resultsAdvanced' to true to return the gecoded 'location' data with the search result)."},"distance":{"type":"number","description":"Maximum distance from the entered location to the physical address where the resource is availalble (ie. service is delivered). \r\nSet 'OrderByDistance' to true to sort search results from nearest to farthest from enetered location.\r\nDistance is ignored (set by the system to 0) when LocationMode is set to 'Within' because distance is not applicable when searching within a geographic boundary. \r\nDistance is set to 5000, when LocationMode set to 'Serving' or 'ServingOnly' to ensure all resources with assigned with the selected service areas area returned (ie. locations are considered\r\nservice areas when LocationMode set to 'Serving' or 'ServingOnly'). As an example, a service (ie. resource) may be physically located in California but have \r\nservice areas throughout the country (eg. helplines).","format":"int32","default":10},"searchWithinLocationType":{"enum":["Unknown","City","County","PostalCode","State","Country"],"type":"string","description":"Type of the location used to set the geographic boundary for searching for resources when LocationMode set to 'Within'. Values are City, County, PostalCode, State, Country, Unknown.\r\nAs an example, if SearchWithinLocationType is set to 'City' with location set to 'Ventura', resources with a physical location within the \r\ngeographic boundary of the city of Ventura will be returned. if SearchWithinLocationType is set to 'County' with location set to 'Ventura', resources \r\nwith a physical location within the geographic boundary of the county of Ventura will be returned. Default value is 'Unknown'. If value is set to 'Unknown' (or\r\nnot set), the LocationType will be determined using the service."},"skip":{"type":"number","description":"Number of results to skip. Used with Size to page results. Note that the total number of resources that match the search is returned with 'count' in\r\nthe search results, if IncludeTotalCount is set to true.","format":"int32","default":0},"size":{"type":"number","description":"Number of results to be returned. Used with Skip to page results. Note that the total number of resources that match the search is returned with 'count' in\r\nthe search results, if IncludeTotalCount is set to true.","format":"int32","default":10},"includeTotalCount":{"type":"boolean","description":"Set to 'true' to include total number of results available for return. If Size is less than value returned by total count,\r\nuse Skip to get additional results","default":true},"filters":{"type":["array","null"],"items":{"required":["field","value"],"type":"object","properties":{"field":{"minLength":1,"type":"string","description":"The name of the search field to filter on. Fields are:\r\n* idServiceAtLocation\r\n* idOrganization\r\n* idService\r\n* idLocation\r\n* tagsService\r\n* dataOwner\r\n* dataOwnerDisplayName\r\n* targetTerm\r\n* address/city\r\n* address/county\r\n* address/stateProvince\r\n* address/postalCode\r\n* address/country\r\n* taxonomy/taxonomyTerm\r\n* taxonomy/taxonomyCode\r\n* taxonomy/target\r\n* serviceAreas/postalCode\r\n* serviceAreas/city\r\n* serviceAreas/county\r\n* serviceAreas/state\r\n* serviceAreas/country","example":"\r\n            dataOwner\r\n            "},"value":{"description":"The value to filter the field on.","example":["211ventura","211bayarea"]},"operators":{"type":"object","properties":{"assert":{"type":"string","nullable":true},"join":{"type":"string","nullable":true}},"additionalProperties":false,"description":"Operator values add logic to filters. The two values are 'assert' and 'join'. Assert can be set to 'eq' or 'ne'. The default setting is 'eq'. If not set or set to null, the default value is applied programatically.\r\nWhen assert is set to 'ne', search results exclude values set in the filter. As an example, if assert set to 'ne' for the filter 'dataOwner', search results will exclude records with the set dataOwner value. \r\nJoin can be set to 'and' or 'or'. The default setting is 'or'. When join is set to 'and', search results will exclude records that do not include all values for the targeted filter. As an example, if join set to 'and' for\r\ntaxonomy terms 'Food' and 'Shelter', search results will exclude all records that do not have a Food and a Shelter taxonomy term associated to the resource. Important! Most filters only support Join set to 'or'. This is \r\nbecuase most fields include only a single value, and requesting two matching values when only one is available will results in no resources being returned. Refer to the documentation for each filter field to learn more\r\nabout the options for assert and join on each field."}},"additionalProperties":false,"description":"Set the value for a field to filter (scope) the results before search is executed."},"description":"A list of search filters that can be used to control/limit the scope of the search. A search filter has a field and a value. See 'SearchFilter'\r\nfor a list of avaialable fields that can be used to filter searches."},"orderbys":{"type":["array","null"],"items":{"required":["field","value"],"type":"object","properties":{"field":{"minLength":1,"type":"string","description":"The name of the field to use for sorting. Fields are:\r\n* nameOrganization\r\n* nameService\r\n* nameLocation\r\n* nameServiceAtLocation","example":"\r\n            nameOrganization\r\n            "},"value":{"description":"The value that sets the sort order (either ascending or descending order). Values are: \r\n* asc\r\n* desc"}},"additionalProperties":false,"description":"Search Orderby item that identifies the field and order to sort results."},"description":"A list of orderBy items used to sort results. An orderBy item has a field and a value. If OrderByDistance is set to true,\r\na orderBy item is programmatically added and used to sort results. OrderBy items added to the list will be executed in the order \r\nthat they are added to the list, after ordering by distance. As an example, to sort results by organization name in descending order add an orderBy \r\nobject to the orderBys array as follows: {\"field\":\"nameOrganization\", \"value\": \"desc\"}"},"facets":{"type":["array","null"],"items":{"type":"string"},"description":"Facets are fields/values returned with results that can be used to resubmit a search with search filter(s). This feature is used\r\nto implement 'faceted' navigation. Default set to [\"tagsService\", \"taxonomy/taxonomyTermLevel1\", \"taxonomy/taxonomyTermLevel2\", \"address/stateProvince\", \"serviceAreas/valueType\", \"dataOwnerDisplayName\"].\r\nOverride the default count and sorting of facet values by appending count and sort to the field (ie. facetField,count:50,sort:value). Sort by 'value' or 'count'. Use sort:-count to sort in ascending order\r\nof count; use sort:count to sort in desceding order of count. Use sort:-value to sort in descending order of value, and sort:value to sort in ascending order of value. (full example: to return 100 \r\nserviceAreas/valueType facets, set the field to ==> serviceAreas/valueType,count:100,sort:-value). Default setting is 10 values for each facet, sorted by count in descending order.\r\nFields are:\r\n* address/city\r\n* address/county\r\n* address/stateProvince\r\n* address/postalCode\r\n* address/country\r\n* taxonomy/TermLevel1\r\n* taxonomy/TermLevel2\r\n* taxonomy/TermLevel3\r\n* taxonomy/TermLevel4        \r\n* taxonomy/TermLevel5\r\n* taxonomy/TermLevel6\r\n* taxonomy/target\r\n* taxonomy/code\r\n* serviceAreas/valueType\r\n* serviceAreas/value\r\n* tagsService\r\n* dataOwner\r\n* dataOwnerDisplayName"},"searchFields":{"type":["array","null"],"items":{"type":"string"},"description":"List of fields that will be searched using keyword(s). Default set to all fields. Fields are:\r\n* nameOrganization\r\n* nameService\r\n* nameLocation\r\n* nameServiceAtLocation\r\n* alternateNamesOrganization\r\n* alternateNamesService\r\n* alternateNamesLocation\r\n* descriptionService\r\n* descriptionOrganization\r\n\r\nOther fields available for search, but not included in default search:\r\n* taxonomyTerm\r\n* taxonomyCode\r\n* serviceAreas/value\r\n* serviceAreas/valueType"},"selectFields":{"type":["array","null"],"items":{"type":"string"},"description":"List of fields to return in search results. Default set to all fields. Fields are:\r\n* idServiceAtLocation\r\n* idService\r\n* idOrganization\r\n* idLocation\r\n* nameOrganization\r\n* nameService\r\n* nameLocation\r\n* nameServiceAtLocation\r\n* alternateNamesOrganization\r\n* alternateNamesService\r\n* alternateNamesLocation\r\n* descriptionService\r\n* descriptionOrganization\r\n* address\r\n* serviceAreas\r\n* taxonomy\r\n* tagsService\r\n* dataOwner\r\n* dataOwnerDisplayName\r\n\r\nOther fields available for selection, but not returned in default search:\r\n* None. All available fields are returned with default."},"searchMode":{"enum":["All","Any"],"type":"string","description":"Set to 'Any' to match one or more entered search keywords in simple text search. Set to 'All' to match on all search keywords. Default is 'All'."},"locationMode":{"enum":["Within","Near","Serving","ServingOnly"],"type":"string","description":"To search for resources 'near' the location, set LocationMode to 'Near', and 'Distance' to a value greater than 0. \r\nThis will return resources with service delivery locations within the chosen distance from the geographic center (latitude/longitude) of the chosen location.\r\nTo search for resources 'within' the geographic boundary of the location, set LocationMode to 'Within'. \r\nThis will return resources within the boundary (polygon of latitude/longitude values) of the chosen location. \r\nTo search for resources available within a service area (a geographic area that often defines eligibility for service), set LocationMode to 'Serving' or 'ServingOnly'. \r\nServingOnly returns resources available within the chosen location (ie. chosen service area). If SearchWithinLocationMode is set to 'Unknown' (the default value), the geographic location\r\ntype will be determined by the API (eg county, city, etc.). The search will then return resources for service areas that match both the type (eg. county) and the location (eg. Ventura). \r\nLocationMode set to Serving differs from LocationMode set to ServingOnly. Serving return returns resources delivered within the selelect location and geography type, plus all\r\nhigher level service area boundaries. As an example, setting LocationMode to 'ServingOnly', Location to 'Ventura' and SearchWithinLocationType to 'County' will return all resources with a service area of Ventura County. \r\nIf LocationMode is set to 'Serving', resources with a service area of California and United States will also be returned, as Ventura is a service area within the higher \r\nlevel service areas of California (state) and United States (country).\r\nNotes: Distance is ignored when LocationMode is set to 'Within', 'Serving' and 'ServingOnly'. OrderByDistance is ignored when LocationMode is\r\nset to 'Within'. Set 'ResultsAdvanced' to true to inspect programmatics changes made by the API to SearchWithinLocationType if left to default (ie. Unknown)."},"keywordIsTaxonomyCode":{"type":"boolean","description":"Set to false for regular text search. Set to true to search on taxonomy code or taxonomy code with wild card (e.g. BD-1800 or BD-1800*). Wildcard codes return code and any-child codes. Separate multiple codes with comma (eg. BD-1800,LM-200*).","default":false},"keywordIsTaxonomyTerm":{"type":"boolean","description":"Set to false for regular text search. Set to 'true' if keyword is a taxonomy term or taxonomy terms (eg. Food Pantry). Separate multiple terms with comma (Food Pantry,Emergency Shelter). Wildcards cannot be used with terms.","default":false},"orderByDistance":{"type":"boolean","description":"Set to true to order results from nearest to farthest from entered location. OrderByDistance can only be used when locactionMode is set to 'Near', otherwise, will be ignored.","default":true},"resultsAdvanced":{"type":"boolean","description":"Set to 'true' to return all search request and result details, including the geocoded location and the request input data (which may have been programatically modified). \r\nNote: this can help users understand restrictions to search requests implemented through policy, including changes applied to parameter and header arguments."}},"additionalProperties":false,"description":"Configures search request (note: header values can overwrite search request input, in some cases). Refer to documentation of input field and headers for more information)."}}},
    method: "post",
    pathTemplate: "/keyword",
    executionParameters: [{"name":"dataOwners","in":"header"},{"name":"taxonomyCodes","in":"header"},{"name":"taxonomyTerms","in":"header"},{"name":"targetTerms","in":"header"},{"name":"tagsService","in":"header"},{"name":"skip","in":"header"},{"name":"size","in":"header"},{"name":"serviceAreaCountries","in":"header"},{"name":"serviceAreaStates","in":"header"},{"name":"serviceAreaCounties","in":"header"},{"name":"serviceAreaCities","in":"header"},{"name":"serviceAreaPostalCodes","in":"header"},{"name":"addressCountries","in":"header"},{"name":"addressStates","in":"header"},{"name":"addressCounties","in":"header"},{"name":"addressCities","in":"header"},{"name":"addressPostalCodes","in":"header"},{"name":"ids","in":"header"}],
    requestBodyContentType: "application/json",
    securityRequirements: [{"apiKeyHeader":[]},{"apiKeyQuery":[]}]
  }],
  ["get-filters-target-terms-assigned-dataowners-dataowners", {
    name: "get-filters-target-terms-assigned-dataowners-dataowners",
    description: `Returns all service taxonomy target terms (AIRS Y-terms ie. linked terms) assigned to a 211 center(s) resource data (eg. 'Older Adults' is a target term (ie. linked term) to a taxonomy term such as 'Homeless Shelter').

Returned values can be filtered by 211 data owner.

This API returns values that can be used as 'targetTerm' parameter value inputs on the Search/Keyword API operation.`,
    inputSchema: {"type":"object","properties":{"dataOwners":{"type":"string","description":"211 data owner(s) to filter values (e.g. 211ventura or 211ventura,211northcarolina). See DataOwners API fitler operation for 211 center values."}},"required":["dataOwners"]},
    method: "get",
    pathTemplate: "/filters/target-terms-assigned",
    executionParameters: [{"name":"dataOwners","in":"query"}],
    requestBodyContentType: undefined,
    securityRequirements: [{"apiKeyHeader":[]},{"apiKeyQuery":[]}]
  }],
]);

/**
 * Security schemes from the OpenAPI spec
 */
const securitySchemes =   {
    "apiKeyHeader": {
      "type": "apiKey",
      "name": "Api-Key",
      "in": "header"
    },
    "apiKeyQuery": {
      "type": "apiKey",
      "name": "api-key",
      "in": "query"
    }
  };


server.setRequestHandler(ListToolsRequestSchema, async () => {
  const toolsForClient: Tool[] = Array.from(toolDefinitionMap.values()).map(def => ({
    name: def.name,
    description: def.description,
    inputSchema: def.inputSchema
  }));
  return { tools: toolsForClient };
});


server.setRequestHandler(CallToolRequestSchema, async (request: CallToolRequest): Promise<CallToolResult> => {
  const { name: toolName, arguments: toolArgs } = request.params;
  const toolDefinition = toolDefinitionMap.get(toolName);
  if (!toolDefinition) {
    console.error(`Error: Unknown tool requested: ${toolName}`);
    return { content: [{ type: "text", text: `Error: Unknown tool requested: ${toolName}` }] };
  }
  return await executeApiTool(toolName, toolDefinition, toolArgs ?? {}, securitySchemes);
});



/**
 * Type definition for cached OAuth tokens
 */
interface TokenCacheEntry {
    token: string;
    expiresAt: number;
}

/**
 * Declare global __oauthTokenCache property for TypeScript
 */
declare global {
    var __oauthTokenCache: Record<string, TokenCacheEntry> | undefined;
}

/**
 * Acquires an OAuth2 token using client credentials flow
 * 
 * @param schemeName Name of the security scheme
 * @param scheme OAuth2 security scheme
 * @returns Acquired token or null if unable to acquire
 */
async function acquireOAuth2Token(schemeName: string, scheme: any): Promise<string | null | undefined> {
    try {
        // Check if we have the necessary credentials
        const clientId = process.env[`OAUTH_CLIENT_ID_SCHEMENAME`];
        const clientSecret = process.env[`OAUTH_CLIENT_SECRET_SCHEMENAME`];
        const scopes = process.env[`OAUTH_SCOPES_SCHEMENAME`];
        
        if (!clientId || !clientSecret) {
            console.error(`Missing client credentials for OAuth2 scheme '${schemeName}'`);
            return null;
        }
        
        // Initialize token cache if needed
        if (typeof global.__oauthTokenCache === 'undefined') {
            global.__oauthTokenCache = {};
        }
        
        // Check if we have a cached token
        const cacheKey = `${schemeName}_${clientId}`;
        const cachedToken = global.__oauthTokenCache[cacheKey];
        const now = Date.now();
        
        if (cachedToken && cachedToken.expiresAt > now) {
            console.error(`Using cached OAuth2 token for '${schemeName}' (expires in ${Math.floor((cachedToken.expiresAt - now) / 1000)} seconds)`);
            return cachedToken.token;
        }
        
        // Determine token URL based on flow type
        let tokenUrl = '';
        if (scheme.flows?.clientCredentials?.tokenUrl) {
            tokenUrl = scheme.flows.clientCredentials.tokenUrl;
            console.error(`Using client credentials flow for '${schemeName}'`);
        } else if (scheme.flows?.password?.tokenUrl) {
            tokenUrl = scheme.flows.password.tokenUrl;
            console.error(`Using password flow for '${schemeName}'`);
        } else {
            console.error(`No supported OAuth2 flow found for '${schemeName}'`);
            return null;
        }
        
        // Prepare the token request
        let formData = new URLSearchParams();
        formData.append('grant_type', 'client_credentials');
        
        // Add scopes if specified
        if (scopes) {
            formData.append('scope', scopes);
        }
        
        console.error(`Requesting OAuth2 token from ${tokenUrl}`);
        
        // Make the token request
        const response = await axios({
            method: 'POST',
            url: tokenUrl,
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': `Basic ${Buffer.from(`${clientId}:${clientSecret}`).toString('base64')}`
            },
            data: formData.toString()
        });
        
        // Process the response
        if (response.data?.access_token) {
            const token = response.data.access_token;
            const expiresIn = response.data.expires_in || 3600; // Default to 1 hour
            
            // Cache the token
            global.__oauthTokenCache[cacheKey] = {
                token,
                expiresAt: now + (expiresIn * 1000) - 60000 // Expire 1 minute early
            };
            
            console.error(`Successfully acquired OAuth2 token for '${schemeName}' (expires in ${expiresIn} seconds)`);
            return token;
        } else {
            console.error(`Failed to acquire OAuth2 token for '${schemeName}': No access_token in response`);
            return null;
        }
    } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error(`Error acquiring OAuth2 token for '${schemeName}':`, errorMessage);
        return null;
    }
}


/**
 * Executes an API tool with the provided arguments
 * 
 * @param toolName Name of the tool to execute
 * @param definition Tool definition
 * @param toolArgs Arguments provided by the user
 * @param allSecuritySchemes Security schemes from the OpenAPI spec
 * @returns Call tool result
 */
async function executeApiTool(
    toolName: string,
    definition: McpToolDefinition,
    toolArgs: JsonObject,
    allSecuritySchemes: Record<string, any>
): Promise<CallToolResult> {
  try {
    // Validate arguments against the input schema
    let validatedArgs: JsonObject;
    try {
        const zodSchema = getZodSchemaFromJsonSchema(definition.inputSchema, toolName);
        const argsToParse = (typeof toolArgs === 'object' && toolArgs !== null) ? toolArgs : {};
        validatedArgs = zodSchema.parse(argsToParse);
    } catch (error: unknown) {
        if (error instanceof ZodError) {
            const validationErrorMessage = `Invalid arguments for tool '${toolName}': ${error.errors.map(e => `${e.path.join('.')} (${e.code}): ${e.message}`).join(', ')}`;
            return { content: [{ type: 'text', text: validationErrorMessage }] };
        } else {
             const errorMessage = error instanceof Error ? error.message : String(error);
             return { content: [{ type: 'text', text: `Internal error during validation setup: ${errorMessage}` }] };
        }
    }

    // Prepare URL, query parameters, headers, and request body
    let urlPath = definition.pathTemplate;
    const queryParams: Record<string, any> = {};
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    let requestBodyData: any = undefined;

    // Apply parameters to the URL path, query, or headers
    definition.executionParameters.forEach((param) => {
        const value = validatedArgs[param.name];
        if (typeof value !== 'undefined' && value !== null) {
            if (param.in === 'path') {
                urlPath = urlPath.replace(`{${param.name}}`, encodeURIComponent(String(value)));
            }
            else if (param.in === 'query') {
                queryParams[param.name] = value;
            }
            else if (param.in === 'header') {
                headers[param.name.toLowerCase()] = String(value);
            }
        }
    });

    // Ensure all path parameters are resolved
    if (urlPath.includes('{')) {
        throw new Error(`Failed to resolve path parameters: ${urlPath}`);
    }
    
    // Construct the full URL
    const requestUrl = API_BASE_URL ? `${API_BASE_URL}${urlPath}` : urlPath;

    // Handle request body if needed
    if (definition.requestBodyContentType && typeof validatedArgs['requestBody'] !== 'undefined') {
        requestBodyData = validatedArgs['requestBody'];
        headers['content-type'] = definition.requestBodyContentType;
    }


    // Apply security requirements if available
    // Security requirements use OR between array items and AND within each object
    const appliedSecurity = definition.securityRequirements?.find(req => {
        // Try each security requirement (combined with OR)
        return Object.entries(req).every(([schemeName, scopesArray]) => {
            const scheme = allSecuritySchemes[schemeName];
            if (!scheme) return false;
            
            // API Key security (header, query, cookie)
            if (scheme.type === 'apiKey') {
                return !!process.env[`API_KEY_${schemeName.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase()}`];
            }
            
            // HTTP security (basic, bearer)
            if (scheme.type === 'http') {
                if (scheme.scheme?.toLowerCase() === 'bearer') {
                    return !!process.env[`BEARER_TOKEN_${schemeName.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase()}`];
                }
                else if (scheme.scheme?.toLowerCase() === 'basic') {
                    return !!process.env[`BASIC_USERNAME_${schemeName.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase()}`] && 
                           !!process.env[`BASIC_PASSWORD_${schemeName.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase()}`];
                }
            }
            
            // OAuth2 security
            if (scheme.type === 'oauth2') {
                // Check for pre-existing token
                if (process.env[`OAUTH_TOKEN_${schemeName.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase()}`]) {
                    return true;
                }
                
                // Check for client credentials for auto-acquisition
                if (process.env[`OAUTH_CLIENT_ID_${schemeName.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase()}`] &&
                    process.env[`OAUTH_CLIENT_SECRET_${schemeName.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase()}`]) {
                    // Verify we have a supported flow
                    if (scheme.flows?.clientCredentials || scheme.flows?.password) {
                        return true;
                    }
                }
                
                return false;
            }
            
            // OpenID Connect
            if (scheme.type === 'openIdConnect') {
                return !!process.env[`OPENID_TOKEN_${schemeName.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase()}`];
            }
            
            return false;
        });
    });

    // If we found matching security scheme(s), apply them
    if (appliedSecurity) {
        // Apply each security scheme from this requirement (combined with AND)
        for (const [schemeName, scopesArray] of Object.entries(appliedSecurity)) {
            const scheme = allSecuritySchemes[schemeName];
            
            // API Key security
            if (scheme?.type === 'apiKey') {
                const apiKey = process.env[`API_KEY_${schemeName.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase()}`];
                if (apiKey) {
                    if (scheme.in === 'header') {
                        headers[scheme.name.toLowerCase()] = apiKey;
                        console.error(`Applied API key '${schemeName}' in header '${scheme.name}'`);
                    }
                    else if (scheme.in === 'query') {
                        queryParams[scheme.name] = apiKey;
                        console.error(`Applied API key '${schemeName}' in query parameter '${scheme.name}'`);
                    }
                    else if (scheme.in === 'cookie') {
                        // Add the cookie, preserving other cookies if they exist
                        headers['cookie'] = `${scheme.name}=${apiKey}${headers['cookie'] ? `; ${headers['cookie']}` : ''}`;
                        console.error(`Applied API key '${schemeName}' in cookie '${scheme.name}'`);
                    }
                }
            } 
            // HTTP security (Bearer or Basic)
            else if (scheme?.type === 'http') {
                if (scheme.scheme?.toLowerCase() === 'bearer') {
                    const token = process.env[`BEARER_TOKEN_${schemeName.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase()}`];
                    if (token) {
                        headers['authorization'] = `Bearer ${token}`;
                        console.error(`Applied Bearer token for '${schemeName}'`);
                    }
                } 
                else if (scheme.scheme?.toLowerCase() === 'basic') {
                    const username = process.env[`BASIC_USERNAME_${schemeName.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase()}`];
                    const password = process.env[`BASIC_PASSWORD_${schemeName.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase()}`];
                    if (username && password) {
                        headers['authorization'] = `Basic ${Buffer.from(`${username}:${password}`).toString('base64')}`;
                        console.error(`Applied Basic authentication for '${schemeName}'`);
                    }
                }
            }
            // OAuth2 security
            else if (scheme?.type === 'oauth2') {
                // First try to use a pre-provided token
                let token = process.env[`OAUTH_TOKEN_${schemeName.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase()}`];
                
                // If no token but we have client credentials, try to acquire a token
                if (!token && (scheme.flows?.clientCredentials || scheme.flows?.password)) {
                    console.error(`Attempting to acquire OAuth token for '${schemeName}'`);
                    token = (await acquireOAuth2Token(schemeName, scheme)) ?? '';
                }
                
                // Apply token if available
                if (token) {
                    headers['authorization'] = `Bearer ${token}`;
                    console.error(`Applied OAuth2 token for '${schemeName}'`);
                    
                    // List the scopes that were requested, if any
                    const scopes = scopesArray as string[];
                    if (scopes && scopes.length > 0) {
                        console.error(`Requested scopes: ${scopes.join(', ')}`);
                    }
                }
            }
            // OpenID Connect
            else if (scheme?.type === 'openIdConnect') {
                const token = process.env[`OPENID_TOKEN_${schemeName.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase()}`];
                if (token) {
                    headers['authorization'] = `Bearer ${token}`;
                    console.error(`Applied OpenID Connect token for '${schemeName}'`);
                    
                    // List the scopes that were requested, if any
                    const scopes = scopesArray as string[];
                    if (scopes && scopes.length > 0) {
                        console.error(`Requested scopes: ${scopes.join(', ')}`);
                    }
                }
            }
        }
    } 
    // Log warning if security is required but not available
    else if (definition.securityRequirements?.length > 0) {
        // First generate a more readable representation of the security requirements
        const securityRequirementsString = definition.securityRequirements
            .map(req => {
                const parts = Object.entries(req)
                    .map(([name, scopesArray]) => {
                        const scopes = scopesArray as string[];
                        if (scopes.length === 0) return name;
                        return `${name} (scopes: ${scopes.join(', ')})`;
                    })
                    .join(' AND ');
                return `[${parts}]`;
            })
            .join(' OR ');
            
        console.warn(`Tool '${toolName}' requires security: ${securityRequirementsString}, but no suitable credentials found.`);
    }
    

    // Prepare the axios request configuration
    const config: AxiosRequestConfig = {
      method: definition.method.toUpperCase(), 
      url: requestUrl, 
      params: queryParams, 
      headers: headers,
      ...(requestBodyData !== undefined && { data: requestBodyData }),
    };

    // Log request info to stderr (doesn't affect MCP output)
    console.error(`Executing tool "${toolName}": ${config.method} ${config.url}`);
    
    // Execute the request
    const response = await axios(config);

    // Process and format the response
    let responseText = '';
    const contentType = response.headers['content-type']?.toLowerCase() || '';
    
    // Handle JSON responses
    if (contentType.includes('application/json') && typeof response.data === 'object' && response.data !== null) {
         try { 
             responseText = JSON.stringify(response.data, null, 2); 
         } catch (e) { 
             responseText = "[Stringify Error]"; 
         }
    } 
    // Handle string responses
    else if (typeof response.data === 'string') { 
         responseText = response.data; 
    }
    // Handle other response types
    else if (response.data !== undefined && response.data !== null) { 
         responseText = String(response.data); 
    }
    // Handle empty responses
    else { 
         responseText = `(Status: ${response.status} - No body content)`; 
    }
    
    // Return formatted response
    return { 
        content: [ 
            { 
                type: "text", 
                text: `API Response (Status: ${response.status}):\n${responseText}` 
            } 
        ], 
    };

  } catch (error: unknown) {
    // Handle errors during execution
    let errorMessage: string;
    
    // Format Axios errors specially
    if (axios.isAxiosError(error)) { 
        errorMessage = formatApiError(error); 
    }
    // Handle standard errors
    else if (error instanceof Error) { 
        errorMessage = error.message; 
    }
    // Handle unexpected error types
    else { 
        errorMessage = 'Unexpected error: ' + String(error); 
    }
    
    // Log error to stderr
    console.error(`Error during execution of tool '${toolName}':`, errorMessage);
    
    // Return error message to client
    return { content: [{ type: "text", text: errorMessage }] };
  }
}


/**
 * Main function to start the server
 */
async function main() {
// Set up StreamableHTTP transport
  try {
    await setupStreamableHttpServer(server, 3000);
  } catch (error) {
    console.error("Error setting up StreamableHTTP server:", error);
    process.exit(1);
  }
}

/**
 * Cleanup function for graceful shutdown
 */
async function cleanup() {
    console.error("Shutting down MCP server...");
    process.exit(0);
}

// Register signal handlers
process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);

// Start the server
main().catch((error) => {
  console.error("Fatal error in main execution:", error);
  process.exit(1);
});

/**
 * Formats API errors for better readability
 * 
 * @param error Axios error
 * @returns Formatted error message
 */
function formatApiError(error: AxiosError): string {
    let message = 'API request failed.';
    if (error.response) {
        message = `API Error: Status ${error.response.status} (${error.response.statusText || 'Status text not available'}). `;
        const responseData = error.response.data;
        const MAX_LEN = 200;
        if (typeof responseData === 'string') { 
            message += `Response: ${responseData.substring(0, MAX_LEN)}${responseData.length > MAX_LEN ? '...' : ''}`; 
        }
        else if (responseData) { 
            try { 
                const jsonString = JSON.stringify(responseData); 
                message += `Response: ${jsonString.substring(0, MAX_LEN)}${jsonString.length > MAX_LEN ? '...' : ''}`; 
            } catch { 
                message += 'Response: [Could not serialize data]'; 
            } 
        }
        else { 
            message += 'No response body received.'; 
        }
    } else if (error.request) {
        message = 'API Network Error: No response received from server.';
        if (error.code) message += ` (Code: ${error.code})`;
    } else { 
        message += `API Request Setup Error: ${error.message}`; 
    }
    return message;
}

/**
 * Converts a JSON Schema to a Zod schema for runtime validation
 * 
 * @param jsonSchema JSON Schema
 * @param toolName Tool name for error reporting
 * @returns Zod schema
 */
function getZodSchemaFromJsonSchema(jsonSchema: any, toolName: string): z.ZodTypeAny {
    if (typeof jsonSchema !== 'object' || jsonSchema === null) { 
        return z.object({}).passthrough(); 
    }
    try {
        const zodSchemaString = jsonSchemaToZod(jsonSchema);
        const zodSchema = eval(zodSchemaString);
        if (typeof zodSchema?.parse !== 'function') { 
            throw new Error('Eval did not produce a valid Zod schema.'); 
        }
        return zodSchema as z.ZodTypeAny;
    } catch (err: any) {
        console.error(`Failed to generate/evaluate Zod schema for '${toolName}':`, err);
        return z.object({}).passthrough();
    }
}
