'''Defines the TagProcessor base class and useful, concrete, child classes.'''

# Copyright (c) 2016 Ved Vyas

# This file is part of doxytag2zealdb.

# doxytag2zealdb is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# doxytag2zealdb is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with doxytag2zealdb.  If not, see <http://www.gnu.org/licenses/>.

class TagProcessor(object):
    '''
    TagProcessor is a base class for finding specific tags in a BeautifulSoup
    and then extracting information from them to insert into a Zeal
    database. TagProcessors are registered with and then executed by a
    TagfileProcessor.

    The key functionality provided by a TagProcessor is:

    1. A match_criterion method to identify tags of interest
    2. A find generator to yield soup tags that match this criterion
    3. Three methods, get_name, get_entry_type, and get_filename, to extract
    information from the tag that is needed for a Zeal database.

    This base class provides default implementations where possible. Child
    classes should make sure all three categories above are implemented.

    When creating a new TagProcessor, be sure to register it with
    TagfileProcessor.register_tag_processor(...). If it's generally useful, add
    it to the standard registrations in
    TagfileProcessor.init_tag_processors(...).
    '''

    def __init__(self, **kwargs):
        '''Initializer.

        Args:
            **include_parent_scopes: bool. See get_name() for more info.
        '''
        self.include_parent_scopes = kwargs.get('include_parent_scopes', False)

    def match_criterion(self, tag):
        '''Determine if a tag matches a particular criterion.

        Override this to define your own criterion.

        Args:
            tag: A BeautifulSoup Tag to test against the criterion.

        Returns:
            True if the tag satifies the criterion, otherwise False.
        '''
        pass

    def find(self, soup):
        '''Yield tags matching the tag criterion from a soup.

        There is no need to override this if you are satisfied with finding
        tags that match match_criterion.

        Args:
            soup: A BeautifulSoup to search through.

        Yields:
            BeautifulSoup Tags that match the criterion.
        '''
        for tag in soup.recursiveChildGenerator():
            if self.match_criterion(tag):
                yield tag

    def get_name(self, tag):
        '''Extract and return a representative "name" from a tag.

        Override as necessary. get_name's output can be controlled through
        keyword arguments that are provided when initializing a
        TagProcessor. For instance, a member of a class or namespace can have
        its parent scope included in the name by passing
        include_parent_scopes=True to __init__().

        Args:
            tag: A BeautifulSoup Tag that satisfies match_criterion.

        Returns:
            A string that would be appropriate to use as an entry name in a
            Zeal database.
        '''
        name = tag.findChild('name').contents[0]

        if self.include_parent_scopes:
            # Include parent scope in returned name
            parent_tag = tag.findParent()
            if parent_tag.get('kind') in ['class', 'struct', 'namespace']:
                name = parent_tag.findChild('name').contents[0] + '::' + name

        return name

    def get_entry_type(self, tag):
        '''Extract and return a representative "entry type" from a tag.

        Override as necessary.

        Args:
            tag: A BeautifulSoup Tag that satisfies match_criterion.

        Returns:
            A string that would be appropriate to use as an entry type in a
            Zeal database.
        '''
        pass

    def get_filename(self, tag):
        '''Extract and return a documentation filename from a tag.

        Override as necessary, though this default implementation probably
        covers all the cases of interest.

        Args:
            tag: A BeautifulSoup Tag that satisfies match_criterion.

        Returns:
            A string that would be appropriate to use as the documentation
            filename for an entry in a Zeal database.
        '''
        if tag.find('filename', recursive=False) is not None:
            return tag.filename.contents[0]
        elif tag.find('anchorfile', recursive=False) is not None:
            return tag.anchorfile.contents[0] + '#' + tag.anchor.contents[0]


class TagProcessorWithEntryTypeAndFindByNamePlusKind(TagProcessor):
    '''A convenient TagProcessor subclass for cases where get_entry_type should
    return the same thing for all (matching) tags and where matching tags are
    identified by their name and "kind" attribute.
    '''

    def __init__(self, entry_type, tag_name, tag_kind, **kwargs):
        '''Initializer.

        Args:
            entry_type: A string that should be returned by get_entry_type()
                for all (matching) tags.
            tag_name: The unicode string name that matching tags should have.
            tag_kind: The unicode string "kind" attribute that matching tags
                should have.
        '''
        super(TagProcessorWithEntryTypeAndFindByNamePlusKind,
              self).__init__(**kwargs)

        # Save this to return from get_entry_type override
        self.entry_type = entry_type

        # Save these for use in match_criterion override
        self.reference_tag_name = tag_name
        self.reference_tag_kind = tag_kind

    def match_criterion(self, tag):
        '''Override. Determine if a tag has the desired name and kind attribute
        value.

        Args:
            tag: A BeautifulSoup Tag.

        Returns:
            True if tag has the desired name and kind, otherwise False.
        '''
        return tag.name == self.reference_tag_name and \
            tag.attrs.get('kind', '') == self.reference_tag_kind

    def get_entry_type(self, tag):
        '''Override. Return entry type this instance was initialized with.

        Args:
            tag: A BeautifulSoup Tag that satisfies match_criterion.

        Returns:
            string entry type that this instance was initialized with.
        '''
        return self.entry_type


class TagProcessorWithAutoEntryTypeAndFindByNamePlusAutoKind(
        TagProcessorWithEntryTypeAndFindByNamePlusKind):
    '''
    This class attempts to provide further convenience by automatically
    determining the entry type and tag kind attribute from the class name. So
    subclass "fooTagProcessor" will have "Foo" automatically extracted as the
    entry type and "foo" automatically extracted as the tag kind attribute when
    it calls its superclass initializer.
    '''

    def __init__(self, tag_name, **kwargs):
        '''Initializer.

        Args:
            tag_name: unicode string name of tag to match. Usually u'compound'
                or u'member'.
        '''
        # Extract entry type from class name, assuming that it is of the format
        # "$(entry_type)TagProcessor"
        class_name = type(self).__name__
        end_idx = class_name.rfind('TagProcessor')

        tag_kind = unicode(class_name[:end_idx])
        entry_type = tag_kind.capitalize()

        # Also assume that the matching tag kind attribute is the same as the
        # entry type
        super(TagProcessorWithAutoEntryTypeAndFindByNamePlusAutoKind,
              self).__init__(entry_type, tag_name, tag_kind, **kwargs)


class TagProcessorWithAutoStuffAndCompoundTagName(
        TagProcessorWithAutoEntryTypeAndFindByNamePlusAutoKind):
    '''
    This subclass goes a step further and hard-codes the name of matching tags
    to u"compound".
    '''

    def __init__(self, **kwargs):
        super(TagProcessorWithAutoStuffAndCompoundTagName, self).__init__(
            u'compound', **kwargs)


class TagProcessorWithAutoStuffAndMemberTagName(
        TagProcessorWithAutoEntryTypeAndFindByNamePlusAutoKind):
    '''
    This subclass goes a step further and hard-codes the name of matching tags
    to u"member".
    '''

    def __init__(self, **kwargs):
        super(TagProcessorWithAutoStuffAndMemberTagName, self).__init__(
            u'member', **kwargs)


class classTagProcessor(TagProcessorWithAutoStuffAndCompoundTagName):
    '''Process class tags.'''
    pass


class fileTagProcessor(TagProcessorWithAutoStuffAndCompoundTagName):
    '''Process file tags.'''

    def get_filename(self, tag):
        '''Override. Get correct documentation filename from a file tag.

        Args:
            tag: A BeautifulSoup Tag for a file.

        Returns:
            A string containing the correct documentation filename from the
            tag.
        '''
        return super(fileTagProcessor, self).get_filename(tag) + '.html'


class namespaceTagProcessor(TagProcessorWithAutoStuffAndCompoundTagName):
    '''Process namespace tags.'''
    pass


class structTagProcessor(TagProcessorWithAutoStuffAndCompoundTagName):
    '''Process struct tags.'''
    pass


class unionTagProcessor(TagProcessorWithAutoStuffAndCompoundTagName):
    '''Process union tags.'''
    pass


class functionTagProcessor(TagProcessorWithAutoStuffAndMemberTagName):
    '''Process function tags.'''

    def __init__(self, **kwargs):
        '''Initializer.

        Args:
            **include_function_signatures: bool. See get_name() for more info.
        '''
        super(functionTagProcessor, self).__init__(**kwargs)

        self.include_function_signatures = kwargs.get(
            'include_function_signatures', False)

    def get_name(self, tag):
        '''Override. Extract a representative "name" from a function tag.

        get_name's output can be controlled through keyword arguments that are
        provided when initializing a functionTagProcessor. For instance,
        function arguments and return types can be included by passing
        include_function_signatures=True to __init__().

        Args:
            tag: A BeautifulSoup Tag for a function.

        Returns:
            A string that would be appropriate to use as an entry name for a
            function in a Zeal database.
        '''
        name = super(functionTagProcessor, self).get_name(tag)

        if self.include_function_signatures:
            # Include complete function signature in returned name
            func_args = tag.findChild('arglist')
            if func_args and len(func_args.contents):
                name += func_args.contents[0]

            ret_type = tag.findChild('type')
            if ret_type and len(ret_type.contents):
                name += ' -> ' + ret_type.contents[0]

        return name

    def get_entry_type(self, tag):
        '''Override that returns u'Method' for class/struct methods.

        Override as necessary.

        Args:
            tag: A BeautifulSoup Tag for a function.

        Returns:
            If this is a class/struct method, returns u'Method', otherwise
            returns the value from the inherited implementation of
            get_entry_type (which should be u'Function').
        '''

        if tag.findParent().get('kind') in ['class', 'struct']:
            return u'Method'

        return super(functionTagProcessor, self).get_entry_type(tag)


class defineTagProcessor(TagProcessorWithAutoStuffAndMemberTagName):
    '''Process #define tags.'''
    pass


class enumerationTagProcessor(TagProcessorWithAutoStuffAndMemberTagName):
    '''Process enumeration tags.'''

    def __init__(self, **kwargs):
        '''Initializer. Utilizes inherited machinery, then manually tweaks the
        entry type to be one of the types supported by Dash (see README).'''
        super(enumerationTagProcessor, self).__init__(**kwargs)
        self.entry_type = u'Enum'


class enumvalueTagProcessor(TagProcessorWithAutoStuffAndMemberTagName):
    '''Process enumeration value tags.'''

    def __init__(self, **kwargs):
        '''Initializer. Utilizes inherited machinery, then manually tweaks the
        entry type to be one of the types supported by Dash (see README).'''
        super(enumvalueTagProcessor, self).__init__(**kwargs)
        self.entry_type = u'Value'


class typedefTagProcessor(TagProcessorWithAutoStuffAndMemberTagName):
    '''Process typedef tags.'''

    def __init__(self, **kwargs):
        '''Initializer. Utilizes inherited machinery, then manually tweaks the
        entry type to be one of the types supported by Dash (see README).'''
        super(typedefTagProcessor, self).__init__(**kwargs)
        self.entry_type = u'Type'


class variableTagProcessor(TagProcessorWithAutoStuffAndMemberTagName):
    '''Process variable tags.'''
    pass
