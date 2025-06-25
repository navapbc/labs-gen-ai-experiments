# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field, StrictStr
from typing import Any, Dict, List, Optional
from typing_extensions import Annotated
from openapi_server.models.data_owner_dto import DataOwnerDto
from openapi_server.security_api import get_token_apiKeyQuery, get_token_apiKeyHeader

class BaseFiltersApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseFiltersApi.subclasses = BaseFiltersApi.subclasses + (cls,)
    async def get_filters_data_owners(
        self,
    ) -> List[DataOwnerDto]:
        """Returns all 211 center data owners and data owners display name values. A 211 data owner is the creator or steward of the resource data.   Returned values can be used in the &#39;dataOwners&#39; parameter of the Search/Keyword API operation (GET and POST methods).    Example 1: Use the results to create a search filter that can be added to the search filters in the of the Search/Keyword API operation (POST method) to filter service at location resources (eg. {\&quot;field\&quot;: \&quot;dataOwner\&quot;, \&quot;value\&quot;: [\&quot;211ventura\&quot;,\&quot;211northcarolina\&quot;]} ).    Example 2: Use the results to create a search filter that can be added to the search filters in the of the Search/Keyword API operation (POST method) to filter service at location resources (eg. {\&quot;field\&quot;: \&quot;dataOwnerDisplayName\&quot;, \&quot;value\&quot;: [\&quot;211 Ventura\&quot;,\&quot;211 North Carolina\&quot;]} )."""
        ...


    async def get_filters_location_values_type_type_dataowners_dataowners(
        self,
        type: Annotated[StrictStr, Field(description="geography type to filter location values (eg. locality, postalCode, county, state, country). Multiple types not supported.")],
        data_owners: Annotated[StrictStr, Field(description="data owner(s) to filter value (e.g. 211ventura OR 211ventura,211northcarolina). See DataOwners API fitler operation for 211 center values.")],
        type_filter: Annotated[Optional[StrictStr], Field(description="geography type to filter type values (e.g. state). Multiple types not supported.")],
        type_filter_values: Annotated[Optional[StrictStr], Field(description="value(s) used by type filtergeography type to filter location values (eg. North Carolina OR North Carolina, California). Multiple values supported.")],
    ) -> List[str]:
        """Returns a list of distinct location values for a given geography type (e.g. county). A location is where a service is delivered. Possible values are: locality, postalCode, county, state, country.    Returned values can be used in the locationAddresses parameter on the Search/Keyword API operation (POST method method).     Example: enter &#39;county&#39; as &#39;type&#39; and &#39;211ventura&#39; as &#39;dataOwners&#39; to return a complete list of all counties assigned to 211ventura locations. Use the typeFilter and typeFilterValue to filter a dataOwner(s)   location values on one or more higher geographical types. As an example, 211 North Carolina has locations outside the state of North Carolina assigned to several of its resources. Without a filter, locations outside   of North Carolina will be returned. Remove values for locations outside of North Carolina by setting the &#39;typeFilter&#39; to &#39;state&#39; and &#39;typeFilterValues&#39; to &#39;NC&#39;. Set multiple values for typeFilterValues by separating values with a comma (e.g. NC,CA).    Use the results to create a search filter for the Search/Keyword API operation (POST method) (eg. {\&quot;field\&quot;: \&quot;address/county\&quot;, \&quot;value\&quot;: [{\&quot;type\&quot;: \&quot;county\&quot;,\&quot;value\&quot;: \&quot;Ventura\&quot;},{\&quot;type\&quot;: \&quot;county\&quot;,\&quot;value\&quot;: \&quot;San Luis Obispo\&quot;}]} )."""
        ...


    async def get_filters_service_area_values_type_type_dataowners_dataowners(
        self,
        type: Annotated[StrictStr, Field(description="geography type to filter service area values (eg. locality, postalCode, county, state, country). Multiple type values not supported.")],
        data_owners: Annotated[StrictStr, Field(description="211 data owner(s) to filter service area values (e.g. 211ventura OR 211ventura,211northcarolina). See DataOwners API fitler operation for 211 center values.")],
        type_filter: Annotated[Optional[StrictStr], Field(description="geography type to filter type values (e.g. state). Multiple types not supported.")],
        type_filter_values: Annotated[Optional[StrictStr], Field(description="value(s) used by type filtergeography type to filter location values (eg. North Carolina OR North Carolina, California). Multiple values supported.")],
    ) -> List[str]:
        """Returns a list of service area values for a given geography type (e.g. county). Type values are: locality, postalCode, county, state, country.    A service area is the geographic area that a service is available. Returned values can be used in the service areas filter on the Search/Keyword API operation (POST method only).    Enter the &#39;scope&#39; value to filter values to the geographic area type (eg. county). Enter the &#39;dataOwners&#39; value(s) to filter values on the entered 211 data owner(s) (eg. 211ventura or 211ventura,211northcarolina).   Refer to the DataOwners filter for a list of 211 data owner(s) that can be used.     Use the typeFilter and typeFilterValue to filter a dataOwner(s) service area values on one or more higher geographical types. As an example, 211 North Carolina has service areas outside the state of North Carolina assigned to several of its resources. Without a filter, service areas outside   of North Carolina will be returned. Remove values for service areas outside of North Carolina by setting the &#39;typeFilter&#39; to &#39;state&#39; and &#39;typeFilterValues&#39; to &#39;North Carolina&#39;. Set multiple values for typeFilterValues by separating values with a comma (e.g. North Carolina,California).    Example: enter &#39;county&#39; as &#39;type&#39; and &#39;211ventura&#39; as &#39;dataOwners&#39; to return a complete list of all service area county values. Use the results to create a search filter that can be added to the search filters   in the the Search/Keyword API operation (POST method) to filter service at location resources (eg. {\&quot;field\&quot;: \&quot;serviceAreas\&quot;, \&quot;value\&quot;: [{\&quot;type\&quot;: \&quot;county\&quot;,\&quot;value\&quot;: \&quot;Ventura\&quot;},{\&quot;type\&quot;: \&quot;county\&quot;,\&quot;value\&quot;: \&quot;San Luis Obispo\&quot;}]} )."""
        ...


    async def get_filters_tags_dataowners_dataowners(
        self,
        data_owners: Annotated[StrictStr, Field(description="211 data owner(s) to filter values (e.g. 211ventura or 211ventura,211northcarolina).  See DataOwners API fitler operation for 211 center values.")],
    ) -> List[str]:
        """Returns all tags for selected 211 data owner(s).    This API provides the caller with values that can be used in the tags parameter of the Search/Keywords API operation."""
        ...


    async def get_filters_target_terms_assigned_dataowners_dataowners(
        self,
        data_owners: Annotated[StrictStr, Field(description="211 data owner(s) to filter values (e.g. 211ventura or 211ventura,211northcarolina). See DataOwners API fitler operation for 211 center values.")],
    ) -> List[str]:
        """Returns all service taxonomy target terms (AIRS Y-terms ie. linked terms) assigned to a 211 center(s) resource data (eg. &#39;Older Adults&#39; is a target term (ie. linked term) to a taxonomy term such as &#39;Homeless Shelter&#39;).    Returned values can be filtered by 211 data owner.    This API returns values that can be used as &#39;targetTerm&#39; parameter value inputs on the Search/Keyword API operation."""
        ...


    async def get_filters_taxonomy_level2_terms(
        self,
        data_owners: Annotated[Optional[StrictStr], Field(description="211 data owner(s) to filter values (e.g. 211ventura or 211ventura,211northcarolina).               See DataOwner API fitler operation for 211 center values. Leave blank if wanting all level 2 terms for all 211s.")],
    ) -> Dict[str, List[object]]:
        """Returns all level 2 taxonomy term values, grouped by level 1 term. This API operation can be used to create a list of topics and subtopics.    List can be filtered on one or more 211 data owners"""
        ...


    async def get_filters_taxonomy_terms_and_codes_assigned_level_level_levelterm_levelter(
        self,
        level: Annotated[StrictStr, Field(description="taxonomy term level to filter values. Accepted values are: 1, 2, 3, 4, 5 or 6. Multiple levels not supported.")],
        level_term: Annotated[StrictStr, Field(description="filters assigned taxonomy terms by term, in combination with the entered level (eg. Basic Needs). See Taxonomy Terms by Level API operation for possible level term values. Multiple terms not supported.")],
        data_owners: Annotated[StrictStr, Field(description="211 data owner(s) to filter values(e.g. 211ventura or 211ventura,211northcarolina). See DataOwners API fitler operation for 211 center values.")],
    ) -> List[str]:
        """Returns all service taxonomy terms and codes assigned to a 211 center(s) resource data. Returned values can be filtered by selected term and level.    As an example, enter &#39;1&#39; as &#39;level&#39;, &#39;Basic Needs&#39; as &#39;levelTerm&#39;, and &#39;211ventura&#39; as &#39;dataOwners&#39; to return all taxonomy   terms (Level2 through Level6 in this example) assigned to 211ventura resources with a Level 1 term of &#39;Basic Needs&#39;   (ie. returns all resources assigned a taxonomy term with parent term equal to &#39;Basic Needs&#39;.    As another example, enter &#39;2&#39; as &#39;level&#39; and &#39;Food&#39; and &#39;levelTerm&#39;, and &#39;211ventura,211northcarolina&#39; as &#39;dataOwners&#39; to return all taxonomy   terms (Level3 through Level6 in this example) assigned to 211ventura or 211northcarolina resources with a Level 2 term of &#39;Food&#39; (ie. returns all resources assigned a   taxonomy term with parent Level 2 term equal to &#39;Food&#39;.    To return all terms assigned, regardless of level, enter &#39;*&#39; for &#39;level&#39; and &#39;levelTerm&#39;. Note: to return only terms, see Taxonomy Term Values Assigned API operation."""
        ...


    async def get_filters_taxonomy_terms_assigned_level_level_levelterm_levelterm_dataowne(
        self,
        level: Annotated[StrictStr, Field(description="level of taxonomy terms to filter values. Accepted values are: 1, 2, 3, 4, 5 or 6. Multiple levels not supported.")],
        level_term: Annotated[StrictStr, Field(description="level term to filter values, in combination with the entered level (eg. Basic Needs). See Taxonomy Terms by Level API operation for possible level term values. Multiple terms not supported.")],
        data_owners: Annotated[StrictStr, Field(description="211 data owner(s) to filter values (e.g. 211ventura or 211ventura,211northcarolina). See DataOwners API fitler operation for 211 center values.")],
    ) -> List[str]:
        """Returns all child service taxonomy terms assigned to a 211 center(s) resource data for a given parent taxonomy term (eg. &#39;Food&#39; is a child term to parent term &#39;Basic Needs&#39;).   Returned values can be filtered by selected term and level. This API can be used to return values that can be used to find resources indexed at any level below a selected parent.    This API returns values that can be used as &#39;taxonomyTerm&#39; parameter value inputs on the Search/Keyword API operation.     As an example, enter &#39;1&#39; as &#39;level&#39;, &#39;Basic Needs&#39; as &#39;levelTerm&#39;, and &#39;211ventura&#39; as &#39;dataOwners&#39; to return all taxonomy   terms (Level2 through Level6 in this example) assigned to 211ventura resources with a Level 1 term of &#39;Basic Needs&#39; (ie. returns all resources assigned a taxonomy term with parent term equal   to &#39;Basic Needs&#39;.     As another example, enter &#39;2&#39; as &#39;level&#39; and &#39;Food&#39; and &#39;levelTerm&#39;, and &#39;211ventura,211northcarolina&#39; as &#39;dataOwners&#39; to return all taxonomy terms (Level3 through Level6 in this example)   assigned to 211ventura or 211northcarolina resources with a Level 2 term of &#39;Food&#39; (ie. returns all resources assigned a taxonomy term with parent Level 2 term equal to &#39;Food&#39;.  To return all terms assigned,   regardless of level, enter &#39;*&#39; for &#39;level&#39; and &#39;levelTerm&#39;."""
        ...


    async def get_filters_taxonomy_terms_by_level_level_level(
        self,
        level: Annotated[StrictStr, Field(description="level of taxonomy to filter values. Accepted values are: 1, 2, 3, 4, 5 or 6. Multiple levels not supported.")],
        data_owners: Annotated[Optional[StrictStr], Field(description="211 data owner(s) to filter values (e.g. 211ventura or 211ventura,211northcarolina). See DataOwners API fitler operation for 211 center values.")],
    ) -> List[str]:
        """Returns all taxonomy term values at selected level of the AIRS taxonomy tree structure for the selected 211 center(s).     As an example, enter &#39;2&#39; as &#39;level&#39; and &#39;211ventura&#39; as &#39;dataOwners&#39; to return all Level 2 taxonomy terms assigned to 211ventura resources."""
        ...
