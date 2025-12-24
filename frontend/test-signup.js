// Test script to verify signup functionality
// Run with: node test-signup.js

require('dotenv').config({ path: '.env.local' })
const { createClient } = require('@supabase/supabase-js')

console.log('Environment check:')
console.log('SUPABASE_URL:', process.env.NEXT_PUBLIC_SUPABASE_URL ? '✅ Found' : '❌ Missing')
console.log('SUPABASE_KEY:', process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY ? '✅ Found' : '❌ Missing')
console.log()

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY
)

async function testSignup() {
  console.log('Testing signup flow...\n')
  
  const timestamp = Date.now()
  const testEmail = `testuser+${timestamp}@gmail.com` // Valid email format
  const testPassword = 'TestPassword123!'
  const fullName = 'Test User'
  
  console.log('1. Creating auth user...')
  console.log('   Email:', testEmail)
  
  try {
    // Step 1: Create auth user
    const { data: authData, error: authError } = await supabase.auth.signUp({
      email: testEmail,
      password: testPassword,
      options: {
        data: {
          full_name: fullName,
        },
        emailRedirectTo: undefined, // Disable email redirect for testing
      },
    })

    if (authError) {
      console.error('❌ Auth signup failed:', authError.message)
      console.log('   Note: This might be an email configuration issue')
      
      // Check if user was created despite the error
      if (authData?.user) {
        console.log('   ⚠️  User was created anyway, continuing...')
      } else {
        return
      }
    } else {
      console.log('✅ Auth user created!')
    }
    console.log('   User ID:', authData.user?.id)
    console.log('   Email verified:', authData.user?.email_confirmed_at ? 'Yes' : 'No (check email)')
    
    // Step 2: Create user profile
    if (authData.user) {
      console.log('\n2. Creating user profile...')
      
      const nameParts = fullName.trim().split(' ')
      const firstName = nameParts[0] || ''
      const lastName = nameParts.slice(1).join(' ') || ''

      const { data: profileData, error: profileError } = await supabase
        .from('users')
        .insert({
          user_id: authData.user.id,
          first_name: firstName,
          last_name: lastName,
        })
        .select()

      if (profileError) {
        console.error('❌ Profile creation failed:', profileError.message)
        console.error('   Details:', profileError)
        return
      }

      console.log('✅ User profile created!')
      console.log('   Profile data:', profileData)
    }
    
    console.log('\n✅ Signup test completed successfully!')
    console.log('\nTest user credentials:')
    console.log('   Email:', testEmail)
    console.log('   Password:', testPassword)
    console.log('\nNote: Check your email for verification link before logging in.')
    
  } catch (error) {
    console.error('❌ Unexpected error:', error)
  }
}

testSignup()
